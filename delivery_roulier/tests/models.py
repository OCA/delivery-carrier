# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import fields, models

# pylint: disable=consider-merging-classes-inherited


class FakeDeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    delivery_type = fields.Selection(
        selection_add=[("test", "Test Carrier")], ondelete={"test": "set default"}
    )


class Package(models.Model):
    _inherit = "stock.quant.package"

    def _test_get_tracking_link(self):
        return f"http://www.test.com/{self.parcel_tracking}"
