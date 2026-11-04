# Copyright 2024 Onestein (<https://www.onestein.nl>)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl)

from odoo import fields, models


class StockWarehouse(models.Model):
    _inherit = "stock.warehouse"

    sencloud_sender_address_id = fields.Many2one(
        related="partner_id.sencloud_sender_address_id", readonly=False
    )
