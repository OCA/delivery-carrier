# Copyright 2021 Manuel Regidor <manuel.regidor@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, fields, models


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    use_amount_untaxed = fields.Boolean(string="Use amount untaxed")

    def rate_shipment(self, order):
        res = super().rate_shipment(order)
        if (
            hasattr(self, f"{self.delivery_type}_rate_shipment")
            and res["success"]
            and self.free_over
            and self.delivery_type != "base_on_rule"
            and self.use_amount_untaxed
        ):
            # Override the old taxed warning
            res["price"] = res["carrier_price"]
            res["warning_message"] = False
            # Set the new untaxed warning
            if (
                self._compute_currency(
                    order,
                    order._compute_amount_untaxed_without_delivery(),
                    "pricelist_to_company",
                )
                >= self.amount
            ):
                res["warning_message"] = _(
                    "The shipping is free since the order untaxed amount exceeds %.2f.",
                    self.amount,
                )
                res["price"] = 0.0
        return res
