# Copyright 2024 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.onchange("order_line", "partner_id", "partner_shipping_id")
    def onchange_order_line(self):
        res = super().onchange_order_line()
        if self.carrier_id and self.carrier_id.is_manual_price:
            self.recompute_delivery_price = False
        return res
