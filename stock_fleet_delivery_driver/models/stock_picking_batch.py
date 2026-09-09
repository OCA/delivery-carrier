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
    driver_id = fields.Many2one(
        inverse="_inverse_driver_id",
    )

    @api.depends("picking_ids", "picking_ids.vehicle_id")
    def _compute_vehicle_id(self):
        """Compute default vehicle based on how many vehicles are used in pickings."""
        # If the batch has a vehicle_id set, we don't change it.
        for record in self.filtered_domain([("vehicle_id", "=", False)]):
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
        for record in self.filtered("vehicle_id"):
            record.picking_ids.vehicle_id = record.vehicle_id

    @api.depends("picking_ids", "picking_ids.driver_id")
    def _compute_driver_id(self):
        """Compute default driver based on how many vehicles are used in pickings."""
        # If the batch has a driver set, we don't change it.
        for record in self.filtered_domain([("driver_id", "=", False)]):
            driver_count_dict = defaultdict(lambda: 0)
            for picking in record.picking_ids.filtered(
                lambda picking: picking.state not in {"done", "cancel"}
                and picking.driver_id
            ):
                driver_count_dict[picking.driver_id] += 1
            if not driver_count_dict:
                continue
            driver_count_data = sorted(
                list(driver_count_dict.items()),
                key=lambda driver_data: driver_data[1],
                reverse=True,
            )
            record.driver_id = driver_count_data[0][0]

    def _inverse_driver_id(self):
        """Set the driver_id for all pickings in the batch."""
        for record in self.filtered("driver_id"):
            record.picking_ids.driver_id = record.driver_id

    def action_done(self):
        """Ensure vehicle propagation when Batch is done."""
        res = super().action_done()
        if self.vehicle_id:
            # If vehicle_id is set, ensure all pickings in the batch have it.
            self.picking_ids.vehicle_id = self.vehicle_id
        if self.driver_id:
            # If driver_id is set, ensure all pickings in the batch have it.
            self.picking_ids.driver_id = self.driver_id
        return res
