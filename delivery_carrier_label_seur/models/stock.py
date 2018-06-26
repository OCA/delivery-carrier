# -*- coding: utf-8 -*-
# © 2015 FactorLibre - Ismael Calvo <ismael.calvo@factorlibre.com>
# © 2017 PESOL - Angel Moya <angel.moya@pesol.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import logging
from base64 import b64decode
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.addons.queue_job.job import job
from datetime import timedelta
from xml.dom.minidom import parseString
_logger = logging.getLogger(__name__)
try:
    from unidecode import unidecode
except (ImportError, IOError) as err:
    _logger.debug(err)

FINAL_SEUR_TRACKING_STATES = [
    'ENTREGA EFECTUADA',
    'ENTREGADO EN PUNTO',
    'ENTREGADO CAMBIO SIN RETORNO',
]


class ShippingLabel(models.Model):
    _inherit = 'shipping.label'

    @api.model
    def _get_file_type_selection(self):
        """ To inherit to add file type """
        res = super(ShippingLabel, self)._get_file_type_selection()
        res.append(('txt', 'TXT'))
        res = list(set(res))
        return res


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    seur_service_code = fields.Selection(selection='_get_seur_services',
                                         default=False)
    seur_product_code = fields.Selection(selection='_get_seur_products',
                                         default=False)
    file_type = fields.Selection(
        related='carrier_id.seur_config_id.file_type', readonly=True)

    def _get_seur_services(self):
        return self.env['delivery.carrier'].SEUR_SERVICES

    def _get_seur_products(self):
        return self.env['delivery.carrier'].SEUR_PRODUCTS

    @api.onchange('carrier_id')
    def carrier_id_change(self):
        res = super(StockPicking, self).carrier_id_change()
        if not self.carrier_id or self.carrier_id.carrier_type != 'seur':
            return res
        carrier = self.carrier_id
        self.seur_service_code = carrier.seur_service_code
        self.seur_product_code = carrier.seur_product_code
        return res

    def check_zipcode(self):
        if self._context.get('zip_checked'):
            return
        zipcode = (self.partner_id.zip and
                   unidecode(self.partner_id.zip.replace(" ", "")) or
                   self.warn(_('ZIP'), _('partner')))

        if not self._context.get('zipdata'):
            config = self.carrier_id.seur_config_id
            zip_data = config.get_zip_data(zipcode)
            if self.partner_id.city.lower() in \
                    [x['NOM_POBLACION'].lower() for x in zip_data]:
                return
            action = self.env.ref(
                'delivery_carrier_label_seur.action_zipcode_selector_wizard').\
                read()[0]
            action['context'] = {
                'zip_data': zip_data,
                'partner_id': self.partner_id.id
            }
            return action

    @api.multi
    def check_tracking_status(self):
        for picking in self:
            if picking.carrier_id.carrier_type == 'seur':
                ref = picking.carrier_tracking_ref
                if ref:
                    config = picking.carrier_id.seur_config_id
                    result = config.get_tracking_info({'reference': ref})
                    res = parseString(result)
                    msg = ''
                    status = False
                    for situations in res.getElementsByTagName('SITUACIONES'):
                        for sit in \
                                situations.getElementsByTagName('SITUACION'):
                            date = sit.getElementsByTagName(
                                'FECHA_SITUACION')[0].firstChild.data
                            desc = sit.getElementsByTagName(
                                'DESCRIPCION_CLIENTE')[0].firstChild.data
                            msg += "%s | %s\n" % (date, desc)
                            status = desc

                    if status:
                        picking.tracking_status_history = msg
                        picking.tracking_status = status

    @api.model
    def _check_tracking_status_cron(self, days=6):
        pickings = self.search([
            ('carrier_type', '=', 'seur'),
            ('carrier_tracking_ref', '!=', False),
            ('tracking_status', 'not in', FINAL_SEUR_TRACKING_STATES),
            ('date_done', '>', fields.Date.to_string(
                fields.Date.from_string(fields.Date.today(self)) -
                timedelta(days=days)))
        ])
        if pickings:
            pickings.check_tracking_status()
        return super(StockPicking, self)._check_tracking_status_cron()

    def action_generate_carrier_label(self):
        action = self.check_zipcode()
        if action:
            return action
        return super(StockPicking, self).action_generate_carrier_label()

    @api.multi
    def _generate_seur_label(self, package_ids=None):
        self.ensure_one()
        if not self.carrier_id.seur_config_id:
            raise UserError(_('No SEUR Config defined in carrier'))
        if not self.picking_type_id.warehouse_id.partner_id:
            raise UserError(
                _('Please define an address in the %s warehouse') % (
                    self.warehouse_id.name))

        seur_context = {
            'printer': 'ZEBRA',
            'printer_model': 'LP2844-Z',
            'ecb_code': '2C',
        }

        if self.file_type == 'pdf':
            seur_context['pdf'] = True

        config = self.carrier_id.with_context(seur_context).seur_config_id
        data = self._get_label_data()
        tracking_ref = False
        label = False
        error = False
        tracking_ref, label, error = config.create_delivery(data)

        self.carrier_tracking_ref = tracking_ref

        if self.file_type == 'pdf' and label:
            label = label.decode('base64')

        if error:
            raise UserError(
                _('Error sending label to SEUR\n%s') % error)
        if tracking_ref and label:
            if self.file_type == 'txt':
                self.with_delay(priority=1).print_seur_document(config, label)
            return {
                'name':
                self.name + '_' + tracking_ref + '.' + self.file_type,
                'file': label,
                'file_type': self.file_type
            }
        else:
            return False

    def _get_label_data(self):
        partner = self.partner_id
        if not self.seur_service_code or not self.seur_product_code:
            raise UserError(_(
                'Please select SEUR service and product codes in picking'))
        international = False
        warehouse = self.picking_type_id and \
            self.picking_type_id.warehouse_id or False

        if self.partner_id and self.partner_id.country_id and \
            self.partner_id.country_id.code and warehouse and \
            warehouse.partner_id and warehouse.partner_id.country_id and \
            warehouse.partner_id.country_id.code and \
            self.partner_id.country_id.code != warehouse.partner_id.\
                country_id.code:
            international = True
        data = {
            'servicio': unidecode(self.seur_service_code),
            'product': unidecode(self.seur_product_code),
            'total_bultos': self.number_of_packages or '1',
            'total_kilos': self.weight or '1',
            'peso_bulto': self.weight or '1',
            'observaciones': self.note and unidecode(self.note) or '',
            'referencia_expedicion': unidecode(self.name),
            'ref_bulto': '',
            'direccion_remitente': warehouse.partner_id.street,
            'clave_portes': 'F',
            'clave_reembolso': '',
            'valor_reembolso': '',
            'cliente_nombre': unidecode(partner.name),
            'cliente_direccion': unidecode(
                ' '.join([partner.street or '', partner.street2 or ''])),
            'cliente_tipovia': 'CL',
            'cliente_tnumvia': 'N',
            'cliente_numvia': ' ',
            'cliente_escalera': '',
            'cliente_piso': '',
            'cliente_puerta': '',
            'cliente_poblacion': partner.city,
            'cliente_cpostal': unidecode(self.partner_id.zip.replace(" ", "")),
            'cliente_pais': unidecode(partner.country_id.code),
            'cliente_email': partner.email and unidecode(partner.email) or '',
            'cliente_telefono': (partner.phone or partner.mobile) and
            unidecode(partner.phone or partner.mobile) or '',
            'cliente_fijo': partner.phone and unidecode(partner.phone) or '',
            'cliente_movil':
            partner.mobile and unidecode(partner.mobile) or '',
            'cliente_atencion': unidecode(self.partner_id.name),
            'id_mercancia': international and '400' or '',
        }
        return data

    def warn(self, field, for_str):
        raise UserError(
            _('Please, enter a %s for %s') % (field, for_str))

    @api.multi
    def generate_default_label(self, package_ids=None):
        """ Add label generation for SEUR """
        self.ensure_one()
        if self.carrier_id.carrier_type == 'seur':
            return self._generate_seur_label(package_ids=package_ids)
        return super(StockPicking, self).generate_default_label(
            package_ids=package_ids)

    def reprint_label(self):
        self.ensure_one()
        if self.carrier_id.carrier_type != 'seur':
            raise UserError(_('Not implemented'))
        config = self.carrier_id.seur_config_id
        if self.file_type == 'txt':
            attachment = self.env['ir.attachment'].search([
                ('res_model', '=', 'stock.picking'),
                ('res_id', '=', self.id),
                ('name', '=', self.name + '_' + self.carrier_tracking_ref +
                 '.' + self.file_type)
            ])
            if not attachment:
                raise UserError(_('Txt seur label not found'))
            label = b64decode(attachment.datas)
            self.with_delay(priority=1).print_seur_document(
                config, label)

    @job
    def print_seur_document(self, config, label):
        # FIX temporal
        label = label.replace('^CI10', '^CI28')
        config.printer.print_document(
            report=None, content=label, format='raw')
