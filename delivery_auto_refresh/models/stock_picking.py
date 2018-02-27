# -*- coding: utf-8 -*-
# Copyright 2018 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def _add_delivery_cost_to_so(self):
        """Update delivery price in SO from picking data."""
        res = super(StockPicking, self)._add_delivery_cost_to_so()
        self.ensure_one()
        sale_order = self.sale_id
        if not sale_order or not self.carrier_id:  # pragma: no cover
            return res
        total = weight = volume = quantity = 0
        for packop in self.pack_operation_ids.filtered('qty_done'):
            if not packop.product_id:
                continue
            move = packop.linked_move_operation_ids[:1].move_id
            qty = move.product_uom._compute_quantity(
                packop.qty_done, packop.product_id.uom_id,
            )
            weight += (packop.product_id.weight or 0.0) * qty
            volume += (packop.product_id.volume or 0.0) * qty
            quantity += qty
            total += move.procurement_id.sale_line_id.price_unit * qty
        total = sale_order.currency_id.with_context(
            date=sale_order.date_order
        ).compute(total, sale_order.company_id.currency_id)
        so_line = sale_order.order_line.filtered(lambda x: x.is_delivery)[:1]
        if so_line:
            so_line.price_unit = self.carrier_id.get_price_from_picking(
                total, weight, volume, quantity,
            )
        return res
