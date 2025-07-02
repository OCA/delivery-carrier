# Copyright 2025 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)


from odoo import fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    estimated_shipping_weight = fields.Float(
        compute="_compute_estimated_picking_weight"
    )

    def _compute_estimated_picking_weight(self):
        for record in self:
            record.estimated_shipping_weight = sum(
                self.move_ids.mapped("estimated_shipping_weight")
            )
