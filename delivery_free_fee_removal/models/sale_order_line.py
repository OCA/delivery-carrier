# Copyright 2020 Camptocamp
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    is_free_delivery = fields.Boolean(compute="_compute_is_free_delivery", store=True,)

    @api.depends("is_delivery", "currency_id", "price_total")
    def _compute_is_free_delivery(self):
        for line in self:
            line.is_free_delivery = line.is_delivery and line.currency_id.is_zero(
                line.price_total
            )

    @api.depends("is_free_delivery")
    def _get_to_invoice_qty(self):
        free_delivery_lines = self.filtered("is_free_delivery")
        free_delivery_lines.qty_to_invoice = 0
        other_lines = self - free_delivery_lines
        super(SaleOrderLine, other_lines)._get_to_invoice_qty()
