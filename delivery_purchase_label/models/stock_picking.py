# Copyright 2024 Michael Tietz (MT Software) <mtietz@mt-software.de>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)
from odoo import fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    delivery_label_purchase_id = fields.Many2one(
        "purchase.order", string="Delivery label purchase order", ondelete="cascade"
    )
