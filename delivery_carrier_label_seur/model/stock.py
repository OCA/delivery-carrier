# -*- coding: utf-8 -*-
# © 2015 FactorLibre - Ismael Calvo <ismael.calvo@factorlibre.com>
# © 2017 PESOL - Angel Moya <angel.moya@pesol.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import logging
from unidecode import unidecode
# from urllib2 import HTTPError

from openerp import models, fields, api, exceptions
from openerp.tools.translate import _

_logger = logging.getLogger(__name__)
try:
    from seur.picking import Picking
except ImportError:
    _logger.debug('Can not `from seur.picking import Picking`.')


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

    seur_service_code = fields.Selection(
        selection='_get_seur_services', string='Seur Service Code',
        default=False)
    seur_product_code = fields.Selection(
        selection='_get_seur_products', string='Seur Product Code',
        default=False)

    @api.model
    def create(self, vals):
        res = super(StockPicking, self).create(vals)
        if 'carrier_id' in vals:
            res.carrier_id_change()
        return res

    @api.one
    def write(self, vals):
        res = super(StockPicking, self).write(vals)
        if 'carrier_id' in vals:
            self.carrier_id_change()
        return res

    def _get_seur_services(self):
        return self.env['delivery.carrier'].SEUR_SERVICES

    def _get_seur_products(self):
        return self.env['delivery.carrier'].SEUR_PRODUCTS

    @api.onchange('carrier_id')
    def carrier_id_change(self):
        super(StockPicking, self).carrier_id_change()
        if not self.carrier_id or self.carrier_id.type != 'seur':
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
            'ecb_code': '2C',
        }

        if config.file_type == 'pdf':
            seur_context['pdf'] = True

        data = self._get_label_data()
        tracking_ref = False
        label = False
        with Picking(config.username,
                              config.password,
                              config.vat,
                              config.franchise_code,
                              'Odoo',  # seurid
                              config.integration_code,
                              config.accounting_code,
                              100.0,
                              seur_context) as picking_api:
            tracking_ref, label, error = picking_api.create(data)

            if error:
                raise exceptions.Warning(
                    _('Error sending label to SEUR\n%s') % error)

            self.carrier_tracking_ref = tracking_ref

            if config.file_type == 'pdf':
                label = label.decode('base64')
        if tracking_ref and label:
            return {
                    'name': self.name + '_' + tracking_ref + '.' + config.file_type,
                    'file': label,
                    'file_type': config.file_type
                    }
        else:
            return False

    def _get_label_data(self):
        partner = self.partner_id.parent_id or self.partner_id
        if not self.seur_service_code or not self.seur_product_code:
            raise exceptions.Warning(_(
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
            'peso_bulto': self.shipping_weight or '1',
            'observaciones': self.note and unidecode(self.note) or '',
            'referencia_expedicion': unidecode(self.name),
            'ref_bulto': '',
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
            'cliente_poblacion': unidecode(partner.city or ''),
            'cliente_cpostal': (partner.zip and
                                unidecode(partner.zip.replace(" ", "")) or
                                self.warn(_('ZIP'), _('partner'))),
            'cliente_pais': unidecode(partner.country_id.code),
            'cliente_email': unidecode(partner.email or ''),
            'cliente_telefono': unidecode(
                partner.phone or partner.mobile or ''),
            'cliente_atencion': unidecode(self.partner_id.name),
            'id_mercancia': international and '400' or '',
        }
        return data

    def warn(self, field, for_str):
        raise exceptions.Warning(
            _('Please, enter a %s for %s') % (field, for_str))

    @api.multi
    def generate_default_label(self, package_ids=None):
        """ Add label generation for SEUR """
        self.ensure_one()
        if self.carrier_id.carrier_type == 'seur':
            return self._generate_seur_label(package_ids=package_ids)
        return super(StockPicking, self).generate_default_label(
            package_ids=package_ids)
