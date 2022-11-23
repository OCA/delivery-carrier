# Copyright 2020 Camptocamp
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def action_confirm(self):
        res = super().action_confirm()
        # Invoice all the free delivery line on order confirmation
        # Or the order will never be fully invoiced.
        delivery_lines = self.order_line.filtered(
            lambda line: line.order_id.state == "sale" and line.is_free_delivery
        )
        for line in delivery_lines:
            line.qty_delivered = line.qty_invoiced = line.product_uom_qty
        return res
