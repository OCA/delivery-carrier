# Copyright 2024 Onestein (<https://www.onestein.nl>)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl)

from odoo import fields, models


class SendcloudParcelItem(models.Model):
    _name = "sendcloud.parcel.item"
    _description = "Sendcloud Parcel Items"
    _rec_name = "description"

    description = fields.Char(required=True)
    quantity = fields.Integer()
    weight = fields.Float()
    value = fields.Float()
    hs_code = fields.Char()
    origin_country = fields.Char()
    product_id = fields.Char()
    properties = fields.Char()
    sku = fields.Char()
    return_reason = fields.Char()
    return_message = fields.Char()
    parcel_id = fields.Many2one("sendcloud.parcel", ondelete="cascade")
