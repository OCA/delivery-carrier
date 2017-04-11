# -*- coding: utf-8 -*-
# © 2017 Angel Moya (PESOL)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


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
