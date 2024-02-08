# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import fields, models


class FakeDeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    delivery_type = fields.Selection(
        selection_add=[("test", "Test Carrier")], ondelete={"test": "set default"}
    )

    def test_send_shipping(self, pickings):
        res = []
        for _p in pickings:
            res = res + [{"exact_price": 0.0, "tracking_number": False}]
        return res
