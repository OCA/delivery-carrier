# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 FactorLibre (http://www.factorlibre.com)
#                  Hugo Santos <hugo.santos@factorlibre.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
import urllib
from datetime import datetime
from openerp import models, fields, api, exceptions
from openerp.tools.translate import _
from ..webservice.mrw_api import MrwEnvio


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.multi
    def _generate_mrw_label(self, package_ids=None):
        self.ensure_one()
        if not self.carrier_id.mrw_config_id:
            raise exceptions.Warning(_('No MRW Config defined in carrier'))
        if not self.picking_type_id.warehouse_id.partner_id:
            raise exceptions.Warning(
                _('Please define an address in the %s warehouse') % (
                    self.warehouse_id.name))
        mrw_api = MrwEnvio(self.carrier_id.mrw_config_id)
        client = mrw_api.client
        transm_envio = client.factory.create('TransmEnvioRequest')

        warehouse_address = self.picking_type_id.warehouse_id.partner_id

        pickup_address = transm_envio.DatosRecogida.Direccion
        pickup_address.Via = warehouse_address.street
        if warehouse_address.street2:
            pickup_address.Resto = warehouse_address.street2

        # TODO: Comprobar que hacer con el resto de codigos postales
        # Llevan un formato especial por país
        # - España: Poner los 5 dígitos. (Ej: 05200 para Ávila)
        # - Portugal: Poner sólo los 4 primeros dígitos de los 7.
        #   (Ej: 1200 para Lisboa)
        # - Andorra: Deben ser 5 dígitos, por lo que se pondrá un 0 delante del
        #   mismo (p. ej 00500 para Andorra la Vella)
        pickup_address.CodigoPostal = warehouse_address.zip.zfill(5)
        pickup_address.Poblacion = warehouse_address.city
        pickup_address.Provincia = warehouse_address.state_id.name or ''
        pickup_address.CodigoPais = warehouse_address.country_id.code or ''

        transm_envio.DatosRecogida.Nif = warehouse_address.vat or ''
        transm_envio.DatosRecogida.Nombre = warehouse_address.name
        transm_envio.DatosRecogida.Telefono = warehouse_address.phone or ''

        # TODO: Ver si establecer informacion horarios
        # horario_rango = client.factory.create('HorarioRangoRequest')
        # horario_rango.Desde = '09:30'
        # horario_rango.Hasta = '19:00'
        # transm_envio.DatosRecogida.Horario.Rangos.HorarioRangoRequest.append(
        #     horario_rango)

        shipping_address = transm_envio.DatosEntrega.Direccion
        shipping_address.Via = self.partner_id.street
        shipping_address.Resto = self.partner_id.street2 or ''
        shipping_address.CodigoPostal = self.partner_id.zip
        shipping_address.Poblacion = self.partner_id.city
        shipping_address.Provincia = self.partner_id.state_id.name or ''
        shipping_address.CodigoPais = self.partner_id.country_id.name or ''

        transm_envio.DatosEntrega.Nif = self.partner_id.vat or ''
        transm_envio.DatosEntrega.Nombre = self.partner_id.name or ''
        transm_envio.DatosEntrega.Telefono = self.partner_id.phone or ''

        # Datos Servicio
        service_data = transm_envio.DatosServicio
        service_data.Fecha = datetime.strftime(
            fields.Datetime.from_string(self.date_done), '%d/%m/%Y')
        service_data.Referencia = self.name
        service_data.EnFranquicia = 'N'
        service_data.CodigoServicio = '0200'
        service_data.NumeroBultos = self.number_of_packages or 1
        service_data.Peso = self.weight or 1

        # TODO: Servicio Rembolso
        # Reembolso: indicador opcional de reembolso. Valores posibles:
        # - N: (default) Sin reembolso.
        # - O: Con reembolso comisión en origen.
        # - D: Con reembolso comisión en destino.
        # ImporteReembolso:
        # - importe nominal del reembolso (para envíos con reembolso)

        if self.partner_id.email:
            notification_request = client.factory.create('NotificacionRequest')
            notification_request.CanalNotificacion = "1"
            notification_request.TipoNotificacion = "4"
            notification_request.MailSMS = self.partner_id.email
            service_data.Notificaciones.NotificacionRequest.append(
                notification_request)

        response = client.service.TransmEnvio(transm_envio)
        if response.Estado != '1' and not response.NumeroEnvio:
            raise exceptions.Warning(response.Mensaje)

        label_factory = client.factory.create('EtiquetaEnvioRequest')
        label_factory.NumeroEnvio = response.NumeroEnvio
        label_factory.ReportTopMargin = "1100"
        label_factory.ReportLeftMargin = "650"

        label_response = client.service.EtiquetaEnvio(label_factory)

        if label_response.Estado != '1':
            raise exceptions.Warning(response.Mensaje)

        label = {
            'file': label_response.EtiquetaFile.decode('base64'),
            'file_type': 'pdf',
            'name': response.NumeroEnvio + '.pdf',
        }

        # panel_url = self._get_mrw_label_from_url(response.NumeroEnvio)

        # return {
        #     'type': 'ir.actions.act_url',
        #     'url': panel_url,
        #     'target': 'new',
        # }

        return [label]

    @api.multi
    def _get_mrw_label_from_url(self, shipping_number):
        self.ensure_one()
        mrw_config = self.carrier_id.mrw_config_id

        url = "http://sagec.mrw.es"
        if mrw_config.is_test:
            url = "http://sagec-test.mrw.es"

        params = {
            'Franq': mrw_config.franchise_code,
            'Ab': mrw_config.subscriber_code,
            'Dep': mrw_config.department_code or '',
            'Usr': mrw_config.username,
            'Pwd': mrw_config.password,
            'NumEnv': shipping_number
        }
        url_params = urllib.urlencode(params)

        # Generar etiqueta en Panel
        panel_url = u"{0}/Panel.aspx?{1}".format(url, url_params)
        return panel_url

    @api.multi
    def generate_shipping_labels(self, package_ids=None):
        """ Add label generation for MRW """
        self.ensure_one()
        if self.carrier_id.type == 'mrw':
            return self._generate_mrw_label(package_ids=package_ids)
        return super(StockPicking, self).generate_shipping_labels(
            package_ids=package_ids)
