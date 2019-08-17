# -*- coding: utf-8 -*-
# Copyright 2019 Tecnativa - Victor M.M. Torres
# Copyright 2019 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.depends(
        'pack_operation_product_ids',
        'pack_operation_product_ids.product_id',
        'pack_operation_product_ids.product_qty',
        'pack_operation_product_ids.qty_done')
    def _cal_weight(self):
        with_pack_ops = self.filtered('pack_operation_product_ids')
        for rec in self:
            has_done = any(rec.mapped('pack_operation_product_ids.qty_done'))
            field = 'qty_done' if has_done else 'product_qty'
            rec.weight = sum(rec.pack_operation_product_ids.mapped(
                lambda x: x[field] * x.product_id.weight
            ))
        super(StockPicking, self - with_pack_ops)._cal_weight()

    @api.multi
    def action_calculate_volume(self):
        for rec in self:
            if rec.pack_operation_product_ids:
                has_done = any(
                    rec.mapped('pack_operation_product_ids.qty_done')
                )
                field = 'qty_done' if has_done else 'product_qty'
                rec.volume = sum(rec.pack_operation_product_ids.mapped(
                    lambda x: x[field] * x.product_id.volume
                ))
            else:
                rec.volume = sum(rec.move_lines.mapped(
                    lambda x: x.product_uom_qty * x.product_id.volume
                ))

    def _create_backorder(self, backorder_moves=None):
        """Compute volume on newly created backorders."""
        if backorder_moves is None:
            backorder_moves = []
        backorders = super(StockPicking, self)._create_backorder(
            backorder_moves=backorder_moves,
        )
        backorders.action_calculate_volume()
        return backorders
