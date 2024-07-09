# Copyright 2024 Onestein (<https://www.onestein.nl>)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl)

from odoo import fields, models


class SendcloudReturn(models.Model):
    _name = "sendcloud.return.location"
    _description = "Sendcloud Return Location"

    name = fields.Char()
    sendcloud_code = fields.Integer(required=True)
    country_name = fields.Char()
    company_name = fields.Char()
    address_1 = fields.Char()
    address_2 = fields.Char()
    house_number = fields.Char()
    city = fields.Char()
    postal_code = fields.Char()
    senderaddress_labels = fields.Text(default="[]")
    brand_id = fields.Many2one("sendcloud.brand")
