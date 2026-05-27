# Copyright 2026 Raumschmiede GmbH
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import fields, models


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    delivery_type = fields.Selection(
        selection_add=[("test", "Test Carrier")], ondelete={"test": "set default"}
    )

    def test_send_shipping(self, pickings):
        return [
            {
                "tracking_number": "TESTTRACK",
                "exact_price": 1.0,
            }
        ]

    def test_tracking_state_update(self, picking):
        data = self.env.context.get("track_data") or {}
        for field, value in data.items():
            picking[field] = value
