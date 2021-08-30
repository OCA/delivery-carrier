# Copyright 2021 Camptocamp
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _, api, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _compute_delivery_state(self):
        super()._compute_delivery_state()
        orders = self.filtered(lambda self: not self.delivery_set)
        for order in orders:
            order.delivery_set = any(
                line.is_delivery_extra for line in order.order_line
            )

    @api.onchange("order_line")
    def onchange_order_line_delivery_extra(self):
        delivery_line_extra = self.order_line.filtered("is_delivery_extra")
        if self.recompute_delivery_price and delivery_line_extra:
            warning = {
                "title": _("Delivery misconfiguration"),
                "message": "Line with delivery costs is already added to sale order",
            }
            return {"warning": warning}
