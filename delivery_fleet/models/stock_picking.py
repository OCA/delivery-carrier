# Copyright 2025 Moduon Team S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)

from odoo import api, fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    vehicle_id = fields.Many2one(
        comodel_name="fleet.vehicle",
        compute="_compute_vehicle_id",
        recursive=True,
        store=True,
        readonly=False,
    )

    @api.depends("state", "carrier_id", "move_ids.move_dest_ids.picking_id.vehicle_id")
    def _compute_vehicle_id(self):
        for picking in self:
            if picking.state not in {"done", "cancel"}:
                vehicles = picking.move_ids.mapped(
                    "move_dest_ids.picking_id.vehicle_id"
                )
                picking.vehicle_id = vehicles[:1] or picking.carrier_id.vehicle_id
