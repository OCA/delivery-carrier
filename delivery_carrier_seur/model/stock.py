# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 FactorLibre (http://www.factorlibre.com)
#                  Ismael Calvo <ismael.calvo@factorlibre.com>
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
from openerp import models, fields, api, exceptions
from openerp.tools.translate import _
from seur.picking import Picking
from unidecode import unidecode
from urllib2 import HTTPError


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    seur_service_code = fields.Selection(
        selection='_get_seur_services', string='Seur Service Code', default=False)
    seur_product_code = fields.Selection(
        selection='_get_seur_products', string='Seur Product Code', default=False)


    def _get_seur_services(self):
        return self.env['delivery.carrier'].SEUR_SERVICES

    def _get_seur_products(self):
        return self.env['delivery.carrier'].SEUR_PRODUCTS

    @api.onchange('carrier_id')
    def carrier_id_onchange(self):
        if not self.carrier_id:
            return
        carrier = self.carrier_id
        self.seur_service_code = carrier.seur_service_code
        self.seur_product_code = carrier.seur_product_code

    @api.multi
    def _generate_seur_label(self, package_ids=None):
        self.ensure_one()
        if not self.carrier_id.seur_config_id:
            raise exceptions.Warning(_('No SEUR Config defined in carrier'))
        if not self.picking_type_id.warehouse_id.partner_id:
            raise exceptions.Warning(
                _('Please define an address in the %s warehouse') % (
                    self.warehouse_id.name))

        config = self.carrier_id.seur_config_id

        seur_context = {
            'printer': 'ZEBRA',
            'printer_model': 'LP2844-Z',
            'ecb_code': '2C'
        }
        seur_picking = Picking(
            config.username,
            config.password,
            config.company_id.vat,
            config.franchise_code,
            'odoo',
            config.franchise_code,
            'odoo',
            seur_context
        )
        try:
            connect = seur_picking.test_connection()
            if connect != 'Connection successfully':
                raise exceptions.Warning(
                    _('Error conecting with SEUR:\n%s' % connect))
        except HTTPError, e:
            raise exceptions.Warning(
                _('Error conecting with SEUR try later:\n%s' % e))

        data = self._get_label_data
        reference, label, error = seur_picking.create(data)
        return [label]

    def _get_label_data(self):
        partner = self.partner_id.parent_id if self.partner_id.is_company \
            else self.partner_id
        data = {
            'servicio': self.seur_service_code,
            'product': self.seur_product_code,
            'total_bultos': self.number_of_packages or '1',
            'total_kilos': self.weight or '1',
            'peso_bulto': self.weight_net or '1',
            'observaciones': unidecode(self.note or ''),
            'referencia_expedicion': self.name,
            'ref_bulto': '',
            'clave_portes': 'F',
            'clave_reembolso': 'F',
            'valor_reembolso': self.sale_id.amount_total or '',
            'cliente_nombre': unidecode(partner.name),
            'cliente_direccion': unidecode(partner.street +
                                           (partner.street2 or '')),
            'cliente_tipovia': 'CL',
            'cliente_tnumvia': 'N',
            'cliente_numvia': '',
            'cliente_escalera': '',
            'cliente_piso': '',
            'cliente_puerta': '',
            'cliente_poblacion': unidecode(partner.city),
            'cliente_cpostal': partner.zip,
            'cliente_pais': unidecode(partner.country_id.name),
            'cliente_email': partner.email or '',
            'cliente_telefono': partner.phone or partner.mobile or '',
            'cliente_atencion': unidecode(self.partner_id.name),
        }
        return data

    @api.multi
    def generate_shipping_labels(self, package_ids=None):
        """ Add label generation for SEUR """
        self.ensure_one()
        if self.carrier_id.type == 'seur':
            return self._generate_seur_label(package_ids=package_ids)
        return super(StockPicking, self).generate_shipping_labels(
            package_ids=package_ids)
