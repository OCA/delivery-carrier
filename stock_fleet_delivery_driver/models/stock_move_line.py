# Copyright 2025 Moduon Team S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)

from odoo import fields, models


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    vehicle_id = fields.Many2one(
        related="picking_id.vehicle_id",
        store=True,
    )
