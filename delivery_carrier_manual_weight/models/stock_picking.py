# Copyright 2024 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    is_manual_weight = fields.Boolean(related="carrier_id.is_manual_weight")
    weight_manual = fields.Float(string="Weight (Manual)", digits="Stock Weight")
    shipping_weight_manual = fields.Float(string="Weight for Shipping (Manual)")

    @api.depends("move_ids", "carrier_id", "weight_manual")
    def _cal_weight(self):
        manual_weight = self.filtered(lambda p: p.carrier_id.is_manual_weight)
        for rec in manual_weight:
            rec.weight = rec.weight_manual
        return super(StockPicking, self - manual_weight)._cal_weight()

    @api.depends(
        "move_line_ids.result_package_id",
        "move_line_ids.result_package_id.shipping_weight",
        "weight_bulk",
        "carrier_id",
        "shipping_weight_manual",
    )
    def _compute_shipping_weight(self):
        manual_weight = self.filtered(lambda p: p.carrier_id.is_manual_weight)
        for rec in manual_weight:
            rec.shipping_weight = rec.shipping_weight_manual
        return super(StockPicking, self - manual_weight)._compute_shipping_weight()
