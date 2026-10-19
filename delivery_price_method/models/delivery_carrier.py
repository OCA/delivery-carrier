# Copyright 2020 Trey, Kilobytes de Soluciones
# Copyright 2020 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    price_method = fields.Selection(
        selection=[
            ("carrier", "Carrier obtained price"),
            ("fixed", "Fixed price"),
            ("base_on_rule", "Based on Rules"),
        ],
        default="carrier",
        string="Price method",
    )

    def rate_shipment(self, order):
        # OVERRIDE: rate using ``price_method`` when it's fixed or rule based.
        # Odoo picks the rating method from ``delivery_type``, hence set it to
        # ``price_method`` during the call, in cache only. Writing the stored
        # field on every rating turns the carrier row into a hot spot leading to
        # concurrent update errors.
        if self.price_method in ("fixed", "base_on_rule") and (
            not self.free_over
            or not self.amount
            or self._compute_currency(order, order.amount_total, "pricelist_to_company")
            < self.amount
        ):
            field = self._fields["delivery_type"]
            # Cached value must not be dirty, otherwise ``cache.set`` would drop it
            self.flush_recordset(["delivery_type"])
            delivery_type = self.delivery_type
            self.env.cache.set(self, field, self.price_method)
            try:
                return super().rate_shipment(order)
            finally:
                self.env.cache.set(self, field, delivery_type)
        return super().rate_shipment(order)

    def send_shipping(self, pickings):
        res = super().send_shipping(pickings)
        if self.price_method in ("fixed", "base_on_rule"):
            rates = getattr(self, f"{self.price_method}_send_shipping")(pickings)
            for index, rate in enumerate(rates):
                del rate["tracking_number"]  # remove offending key
                res[index].update(rate)
        return res

    def _get_price_from_picking(self, total, weight, volume, quantity, wv=0.0):
        if (
            self.price_method == "base_on_rule"
            and self.free_over
            and total >= self.amount
        ):
            return 0.0
        return super()._get_price_from_picking(total, weight, volume, quantity, wv)
