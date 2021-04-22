# Copyright 2018 Tecnativa - Sergio Teruel
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import models


class StockMove(models.Model):
    _inherit = "stock.move"

    def get_original_move(self):
        if self.move_dest_ids:
            return self.move_dest_ids.get_original_move()
        return self

    def _get_new_picking_values(self):
        vals = super()._get_new_picking_values()
        original_move = self.get_original_move()
        zone_id = original_move.sale_line_id.order_id.delivery_zone_id.id
        if not zone_id:
            zone_id = (
                self.env["res.partner"]
                .browse(vals.get("partner_id", False))
                .delivery_zone_id.id
            )
        vals["delivery_zone_id"] = zone_id
        return vals
