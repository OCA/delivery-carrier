# Copyright 2024 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def _get_protected_fields(self):
        # Avoid locked orders validation error when voiding the delivery line
        fields = super()._get_protected_fields()
        if self.env.context.get("delivery_auto_refresh_override_locked"):
            return [x for x in fields if x not in ["product_uom_qty", "price_unit"]]
        return fields

    @api.model_create_multi
    def create(self, vals_list):
        lines = super(
            SaleOrderLine, self.with_context(auto_refresh_delivery=True)
        ).create(vals_list)
        for order in lines.order_id:
            order._auto_refresh_delivery()
        return lines

    def write(self, vals):
        res = super(SaleOrderLine, self.with_context(auto_refresh_delivery=True)).write(
            vals
        )
        for order in self.order_id:
            order._auto_refresh_delivery()
        return res
