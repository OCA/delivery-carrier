# Copyright 2024 Onestein (<https://www.onestein.eu>)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl)

from odoo import fields, models


class SendcloudCustomPriceDetailsWizard(models.TransientModel):
    _name = "sendcloud.custom.price.details.wizard"
    _description = "Sendcloud Custom Price Details Wizard"

    shipping_method_country_id = fields.Many2one(
        "sendcloud.shipping.method.country",
        readonly=True,
        required=True,
        string="Shipping to Country",
    )
    price = fields.Float(
        related="shipping_method_country_id.price", string="Standard Price"
    )
    enable_price_custom = fields.Boolean(
        string="Enable custom price?",
        related="shipping_method_country_id.enable_price_custom",
        readonly=False,
    )
    price_custom = fields.Float(
        related="shipping_method_country_id.price_custom",
        readonly=False,
        string="Custom Price",
    )
    price_check = fields.Selection(related="shipping_method_country_id.price_check")
    product_id = fields.Many2one(
        related="shipping_method_country_id.product_id", readonly=False
    )

    def set_custom_price(self):
        self.ensure_one()
        self.shipping_method_country_id.price_custom = self.price_custom
        self.shipping_method_country_id.enable_price_custom = self.enable_price_custom
        self.shipping_method_country_id.product_id = self.product_id

    def remove_custom_price(self):
        self.ensure_one()
        self.env["sendcloud.shipping.method.country.custom"].search(
            [
                ("iso_2", "=", self.shipping_method_country_id.iso_2),
                ("company_id", "=", self.shipping_method_country_id.company_id.id),
                ("method_code", "=", self.shipping_method_country_id.method_code),
            ],
        ).unlink()
