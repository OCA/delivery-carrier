# Copyright 2018 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models
from odoo.tools import safe_eval


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def _add_delivery_cost_to_so(self):
        """Update delivery price in SO from picking data."""
        res = super(StockPicking, self)._add_delivery_cost_to_so()
        get_param = self.env["ir.config_parameter"].sudo().get_param
        param = "delivery_auto_refresh.refresh_after_picking"
        if not safe_eval(get_param(param, "0")):
            return res
        self.ensure_one()
        sale_order = self.sale_id
        if not sale_order or not self.carrier_id:  # pragma: no cover
            return res
        so_line = sale_order.order_line.filtered(lambda x: x.is_delivery)[:1]
        if not so_line:  # pragma: no cover
            return res
        total = weight = volume = quantity = 0
        for move_line in self.move_line_ids.filtered("qty_done"):
            if not move_line.product_id:
                continue
            move = move_line.move_id
            qty = move.product_uom._compute_quantity(
                move_line.qty_done, move_line.product_id.uom_id,
            )
            weight += (move_line.product_id.weight or 0.0) * qty
            volume += (move_line.product_id.volume or 0.0) * qty
            quantity += qty
            total += move.sale_line_id.price_unit * qty
        total = sale_order.currency_id._convert(
            total,
            sale_order.company_id.currency_id,
            sale_order.company_id,
            sale_order.date_order,
        )
        so_line.price_unit = self.carrier_id._get_price_from_picking(
            total, weight, volume, quantity,
        )
        return res
