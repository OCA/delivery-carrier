# Copyright 2024 Onestein (<https://www.onestein.nl>)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl)

from odoo import _, api, fields, models


class SendcloudShippingMethodCountry(models.Model):
    _name = "sendcloud.shipping.method.country"
    _description = "Sendcloud Shipping Method Country"

    name = fields.Char(compute="_compute_country_id")
    country_id = fields.Many2one(
        "res.country", compute="_compute_country_id", string="To Country"
    )
    sendcloud_code = fields.Integer(required=True)
    iso_2 = fields.Char(required=True)
    iso_3 = fields.Char()
    from_name = fields.Char(compute="_compute_country_id")
    from_country_id = fields.Many2one("res.country", compute="_compute_country_id")
    from_iso_2 = fields.Char()
    from_iso_3 = fields.Char()
    price = fields.Float()
    method_code = fields.Integer(required=True)
    sendcloud_is_return = fields.Boolean()
    product_id = fields.Many2one(
        comodel_name="product.product",
        compute="_compute_price_custom",
        inverse="_inverse_price_custom",
        string="Specific Delivery Product",
        domain="[('type', '=', 'service')]",
        help="This product will be used on the sale order line",
        readonly=False,
    )
    company_id = fields.Many2one("res.company", required=True)
    enable_price_custom = fields.Boolean(
        compute="_compute_price_custom",
        inverse="_inverse_price_custom",
        readonly=False,
    )
    price_custom = fields.Float(
        compute="_compute_price_custom",
        inverse="_inverse_price_custom",
        readonly=False,
        string="Custom Price",
        help="This price will override the standard price and will be applied "
        "to the shipping price.",
    )
    price_check = fields.Selection(
        [
            ("standard", "Standard"),
            ("custom", "Custom"),
            ("unavailable", "Unavailable"),
        ],
        compute="_compute_price_custom",
    )

    @api.depends("iso_2", "company_id", "method_code")
    def _compute_price_custom(self):
        isos = self.mapped("iso_2")
        companies = self.mapped("company_id")
        method_codes = self.mapped("method_code")
        custom_items = self.env["sendcloud.shipping.method.country.custom"].search(
            [
                ("iso_2", "in", isos),
                ("company_id", "in", companies.ids),
                ("method_code", "in", method_codes),
            ],
        )
        for item in self:
            custom = custom_items.filtered(
                lambda ci, i=item: ci.iso_2 == i.iso_2
                and ci.method_code == i.method_code
                and ci.company_id == i.company_id
            )
            if custom:
                item.price_check = "custom"
                item.enable_price_custom = custom[0].enable_price_custom
                if custom[0].enable_price_custom:
                    item.price_custom = custom[0].price
                else:
                    item.price_custom = item.price
                item.product_id = custom[0].product_id
            else:
                item.price_custom = item.price
                item.price_check = "standard"

    def _inverse_price_custom(self):
        sendcloud_shipping_method_country_custom_obj = self.env[
            "sendcloud.shipping.method.country.custom"
        ]
        sendcloud_shipping_method_country_custom_vals = []
        for item in self:
            shipping_method_country = (
                sendcloud_shipping_method_country_custom_obj.search(
                    [
                        ("iso_2", "=", item.iso_2),
                        ("company_id", "=", item.company_id.id),
                        ("method_code", "=", item.method_code),
                    ],
                    limit=1,
                )
            )
            if shipping_method_country:
                shipping_method_country.write(
                    {
                        "price": item.price_custom,
                        "product_id": item.product_id.id,
                        "enable_price_custom": item.enable_price_custom,
                    }
                )
            else:
                sendcloud_shipping_method_country_custom_vals.append(
                    {
                        "iso_2": item.iso_2,
                        "company_id": item.company_id.id,
                        "method_code": item.method_code,
                        "price": item.price_custom,
                        "product_id": item.product_id.id,
                        "enable_price_custom": item.enable_price_custom,
                    }
                )
        sendcloud_shipping_method_country_custom_obj.create(
            sendcloud_shipping_method_country_custom_vals
        )

    @api.depends("iso_2", "from_iso_2")
    def _compute_country_id(self):
        iso_2_list = self.mapped("iso_2")
        from_iso_2_list = self.mapped("from_iso_2")
        all_countries = self.env["res.country"].search(
            [("code", "in", iso_2_list + from_iso_2_list)]
        )
        for record in self:
            to_countries = all_countries.filtered(lambda c, r=record: c.code == r.iso_2)
            record.country_id = fields.first(to_countries)
            record.name = record.country_id.name
            from_countries = all_countries.filtered(
                lambda c, r=record: c.code == r.from_iso_2
            )
            record.from_country_id = fields.first(from_countries)
            record.from_name = record.from_country_id.name

    def sendcloud_custom_price_details(self):
        self.ensure_one()
        return {
            "name": _("Custom Price Details"),
            "type": "ir.actions.act_window",
            "res_model": "sendcloud.custom.price.details.wizard",
            "views": [[False, "form"]],
            "target": "new",
            "context": {
                "default_shipping_method_country_id": self.id,
            },
        }
