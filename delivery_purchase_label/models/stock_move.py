# Copyright 2025 Raumschmiede GmbH
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import fields, models


class StockMove(models.Model):
    _inherit = "stock.move"

    delivery_label_purchase_line_id = fields.Many2one(
        "purchase.order.line",
        string="Delivery Label Purchase Order Line",
        ondelete="cascade",
    )

    # Prevent merging delivery label moves
    # from different purchase order lines
    def _prepare_merge_moves_distinct_fields(self):
        distinct_fields = super()._prepare_merge_moves_distinct_fields()
        distinct_fields.append("delivery_label_purchase_line_id")
        return distinct_fields
