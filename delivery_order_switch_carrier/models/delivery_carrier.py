# Copyright 2026 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models
from odoo.tools import config


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    def rate_shipment(self, order):
        res = super().rate_shipment(order)
        test_condition = not config["test_enable"] or (
            config["test_enable"]
            and self.env.context.get("test_delivery_order_switch_carrier")
        )
        if not test_condition:
            return res
        if res["success"]:
            # If a rate has been returned correctly, we overwrite the price only if
            # the shipping line has already been invoiced, to avoid errors (for
            # example, because the price was changed manually on the sale line).
            delivery_lines = order.order_line.filtered("is_delivery")
            invoiced_delivery_lines = delivery_lines.filtered(
                lambda x: x.qty_invoiced > 0
            )
            if invoiced_delivery_lines:
                delivery_line = fields.first(invoiced_delivery_lines)
                res["price"] = delivery_line.price_unit
                if "carrier_price" in res:
                    res["carrier_price"] = res["price"]
        return res
