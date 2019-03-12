# Copyright 2018 Tecnativa - Sergio Teruel
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import models


class StockMove(models.Model):
    _inherit = 'stock.move'

    def _get_new_picking_values(self):
        vals = super()._get_new_picking_values()
        zone_id = self.sale_line_id.order_id.delivery_zone_id.id
        if not self.sale_line_id:
            zone_id = self.env['res.partner'].browse(
                vals.get('partner_id', False)).delivery_zone_id.id
        vals['delivery_zone_id'] = zone_id
        return vals
