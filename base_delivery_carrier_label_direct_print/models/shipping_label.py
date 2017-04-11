# -*- coding: utf-8 -*-
# © 2017 Angel Moya (PESOL)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, models
import base64


class ShippingLabel(models.Model):

    _inherit = 'shipping.label'

    @api.model
    def create(self, values):
        if values.get('direct_print') and values.get('datas'):
            printer = values.get('printer_id') or \
                self.env['printing.printer'].get_default()
            printer.print_document(
                None, base64.b64decode(values.get('datas')), 'raw')
            values.pop('direct_print')
            values.pop('printer_id')
        if values.get('no_attach'):
            return True
        return super(ShippingLabel, self).create(values)
