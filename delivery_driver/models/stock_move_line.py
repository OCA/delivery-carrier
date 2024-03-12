# Copyright 2024 Moduon Team S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)


from odoo import fields, models


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    driver_id = fields.Many2one(
        related="picking_id.driver_id",
        domain="[('is_driver', '=', True)]",
        store="True",
    )
