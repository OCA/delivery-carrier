# Copyright 2024 Onestein (<https://www.onestein.nl>)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl)

from odoo import fields, models


class SendcloudInvoice(models.Model):
    _name = "sendcloud.invoice.item"
    _description = "Sendcloud Invoice Items"

    name = fields.Char()
    sendcloud_code = fields.Integer(required=True)
    sendcloud_invoice_id = fields.Many2one("sendcloud.invoice", ondelete="cascade")
