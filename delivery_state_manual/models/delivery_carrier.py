# Copyright 2024 Alberto Martínez <alberto.martinez@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    delivery_state_manual = fields.Boolean(
        string="Manual Delivery State",
        help="Setting this field will allow users to "
        "manually edit the delivery state field of its pickings. "
        "It will also hide the picking's tracking state fields",
    )

    def send_shipping(self, pickings):
        res = super().send_shipping(pickings)
        if self.delivery_state_manual:
            pickings.write(
                {
                    "delivery_state": False,
                    "date_shipped": False,
                }
            )
        return res
