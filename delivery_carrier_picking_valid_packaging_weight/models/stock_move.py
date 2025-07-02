# Copyright 2025 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import api, fields, models


class StockMove(models.Model):
    _inherit = "stock.move"

    estimated_shipping_weight = fields.Float(
        compute="_compute_estimated_shipping_weight"
    )

    def _get_estimated_shipping_quantity(self):
        self.ensure_one()
        return self.product_uom_qty

    def _compute_estimated_shipping_weight(self):
        for record in self:
            product_qty = record._get_estimated_shipping_quantity()
            weight = record.product_id.get_total_weight_from_packaging(product_qty)
            record.estimated_shipping_weight = weight

    @api.model
    def read_group(
        self,
        domain,
        fields,
        groupby,
        offset=0,
        limit=None,
        orderby=False,
        lazy=True,
    ):
        # Override read_group to calculate the sum of the non-stored fields
        # that depend on the user context
        res = super().read_group(
            domain,
            fields,
            groupby,
            offset=offset,
            limit=limit,
            orderby=orderby,
            lazy=lazy,
        )
        moves = self.env["stock.move"]
        for line in res:
            if "__domain" in line and "estimated_shipping_weight" in fields:
                moves = self.search(line["__domain"])
                line["estimated_shipping_weight"] = sum(
                    moves.mapped("estimated_shipping_weight")
                )
        return res
