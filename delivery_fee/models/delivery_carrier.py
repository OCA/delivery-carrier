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
