# Copyright 2024 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class StockPickingType(models.Model):
    _inherit = "stock.picking.type"

    auto_print_shipping_labels = fields.Boolean(
        help="If this checkbox is ticked, Odoo will automatically print the delivery"
        "shipping labels if they're available",
    )
