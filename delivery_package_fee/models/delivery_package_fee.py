# Copyright 2020 Camptocamp
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class DeliveryPackageFee(models.Model):
    _name = "delivery.package.fee"
    _description = "Delivery Package Fees"

    carrier_id = fields.Many2one(
        comodel_name="delivery.carrier",
        required=True,
        ondelete="cascade",
    )
    product_id = fields.Many2one(
        comodel_name="product.product",
        required=True,
        ondelete="restrict",
    )
