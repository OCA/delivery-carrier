# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import fields, models

# pylint: disable=consider-merging-classes-inherited


class FakeDeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    delivery_type = fields.Selection(
        selection_add=[("test", "Test Carrier")], ondelete={"test": "set default"}
    )
