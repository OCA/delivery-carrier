# Copyright 2020 Camptocamp
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    is_free_delivery = fields.Boolean(compute="_compute_is_free_delivery", store=True)

    @api.depends("is_delivery", "currency_id", "price_total")
    def _compute_is_free_delivery(self):
        for line in self:
            line.is_free_delivery = line.is_delivery and line.currency_id.is_zero(
                line.price_total
            )
