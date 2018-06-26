# -*- coding: utf-8 -*-
# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, api, fields, _
from odoo.exceptions import UserError


class ZipcodeSelectorWizard(models.TransientModel):
    _name = 'zipcode.selector.wizard'

    @api.model
    def _get_default_partner_id(self):
        if 'partner_id' not in self._context:
            raise UserError(_())
        return self._context.get('partner_id')

    @api.model
    def _get_default_zip_options(self):
        if 'zip_data' not in self._context:
            return []
        default_zip_options = []
        for zipcode in self._context.get('zip_data'):
            default_zip_options.append(
                (zipcode['NOM_POBLACION'], zipcode['NOM_POBLACION']))
        return default_zip_options

    partner_id = fields.Many2one(
        'res.partner', 'Customer',
        default=lambda self: self._get_default_partner_id())
    partner_city = fields.Char(
        'Delivery city', related='partner_id.city', readonly=True)
    city_name = fields.Selection(
        lambda self: self._get_default_zip_options(), string='Seur city')

    def confirm(self):
        self.partner_id.city = self.city_name
        picking = self.env['stock.picking'].browse(
            self._context.get('active_id'))
        return picking.with_context(
            zip_checked=True).action_generate_carrier_label()
