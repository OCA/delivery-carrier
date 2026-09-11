# Copyright 2026 Moduon
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
from odoo import fields, models


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    fee_product_id = fields.Many2one(
        comodel_name="product.product",
        ondelete="restrict",
        domain="[('type', '=', 'service')]",
    )
    fee_return_percentage = fields.Float(
        string="Fee return %",
        default=0,
        help="% of the fee to be returned to the customer in case of full return. "
        "E.g.: 0% for no return, 100% for full return",
    )
