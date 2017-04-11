# -*- coding: utf-8 -*-
# © 2017 Angel Moya (PESOL)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models, _
from openerp.exceptions import ValidationError


class DeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'

    direct_print = fields.Boolean(
        string='Direct Print')
    no_attach = fields.Boolean(
        string='No Attach')
    printer_id = fields.Many2one(
        comodel_name='printing.printer',
        string='Printer')

    @api.onchange('direct_print')
    def _onchange_direct_print(self):
        self.no_attach = self.direct_print and self.no_attach

    @api.constrains('direct_print', 'no_attach')
    def _check_field(self):
        if self.no_attach and not self.direct_print:
            raise ValidationError(_(
                "You can not set 'No Attach' and not set 'Direct Print'"
            ))
