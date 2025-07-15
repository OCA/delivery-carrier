# Copyright 2025 Moduon Team S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)

from collections import defaultdict

from odoo import api, fields, models


class StockPickingBatch(models.Model):
    _inherit = "stock.picking.batch"

    vehicle_id = fields.Many2one(
        compute="_compute_vehicle_id",
        inverse="_inverse_vehicle_id",
        store=True,
        readonly=False,
    )

    @api.depends("picking_ids", "picking_ids.vehicle_id")
    def _compute_vehicle_id(self):
        """Compute default vehicle based on how many vehicles are used in pickings."""
        for record in self:
            # If the batch has a vehicle_id set, we don't change it.
            if record.vehicle_id:
                continue
            vehicle_count_dict = defaultdict(lambda: 0)
            for picking in record.picking_ids.filtered(
                lambda picking: picking.state not in {"done", "cancel"}
                and picking.vehicle_id
            ):
                vehicle_count_dict[picking.vehicle_id] += 1
            if not vehicle_count_dict:
                continue
            vehicle_count_data = sorted(
                list(vehicle_count_dict.items()),
                key=lambda vehicle_data: vehicle_data[1],
                reverse=True,
            )
            record.vehicle_id = vehicle_count_data[0][0]

    def _inverse_vehicle_id(self):
        """Set the vehicle_id for all pickings in the batch."""
        for record in self:
            if not record.vehicle_id:
                # If no vehicle is set, skip writing to pickings.
                continue
            record.picking_ids.vehicle_id = record.vehicle_id

    def action_done(self):
        """Ensure vehicle propagation when Batch is done."""
        res = super().action_done()
        if self.vehicle_id:
            # If vehicle_id is set, ensure all pickings in the batch have it.
            self.picking_ids.vehicle_id = self.vehicle_id
        return res
