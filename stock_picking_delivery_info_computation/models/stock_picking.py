# -*- coding: utf-8 -*-
# Copyright 2019 Tecnativa - Victor M.M. Torres
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
            has_done = any(rec.mapped('pack_operation_product_ids.qty_done'))
            field = 'qty_done' if has_done else 'product_qty'
            rec.volume = sum(rec.pack_operation_product_ids.mapped(
                lambda x: x[field] * x.product_id.volume
            ))
            if rec.move_lines and not has_done:
                rec.volume = sum(rec.move_lines.mapped(
                    lambda x: x.product_uom_qty * x.product_id.volume
                ))
