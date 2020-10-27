# Copyright 2019 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    # Needed for fields.Monetary
    currency_id = fields.Many2one(
        related="sale_id.currency_id",
        readonly=True,
        string="Currency",
        related_sudo=True,  # for avoiding access problems
    )
    carrier_price_for_report = fields.Monetary(
        compute="_compute_carrier_price_for_report",
    )

    @api.depends("sale_id", "carrier_price")
    def _compute_carrier_price_for_report(self):
        for picking in self:
            so_lines = picking.sale_id.order_line.filtered("is_delivery")
            if so_lines:
                picking.carrier_price_for_report = sum(so_lines.mapped("price_unit"))
            else:
                picking.carrier_price_for_report = picking.carrier_price
