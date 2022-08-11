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
        string="Price method",
        default="carrier",
    )

    def rate_shipment(self, order):
        """Trick the method for using all the upstream code for the
        price computation in case of using fixed or base_on_rule.
        """
        previous_method = False
        if self.price_method in ("fixed", "base_on_rule"):
            previous_method = self.delivery_type
            self.sudo().delivery_type = self.price_method
        res = super().rate_shipment(order)
        if previous_method:
            self.sudo().delivery_type = previous_method
        return res

    def send_shipping(self, pickings):
        res = super().send_shipping(pickings)
        if self.price_method in ("fixed", "base_on_rule"):
            rates = getattr(self, "%s_send_shipping" % self.price_method)(pickings)
            for index, rate in enumerate(rates):
                del rate["tracking_number"]  # remove offending key
                res[index].update(rate)
        return res
