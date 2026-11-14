# Copyright 2024 Onestein (<https://www.onestein.eu>)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl)

from odoo import fields, models


class SendcloudShippingMethodCountryCustom(models.Model):
    _name = "sendcloud.shipping.method.country.custom"
    _description = "Sendcloud Shipping Method Country Custom"

    iso_2 = fields.Char(required=True)
    custom_price = fields.Boolean()
    enable_price_custom = fields.Boolean()
    price = fields.Float()
    method_code = fields.Integer(required=True)
    company_id = fields.Many2one("res.company", required=True)
    product_id = fields.Many2one(
        comodel_name="product.product",
        string="Specific Delivery Product",
        domain="[('type', '=', 'service')]",
        help="This product will be used on the sale order line",
    )
