# Copyright 2025 Moduon Team S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)

from odoo import api, fields, models
from odoo.osv import expression


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

    def _get_possible_pickings_domain(self):
        domain = super()._get_possible_pickings_domain()
        if self.picking_type_id.batch_group_by_vehicle:
            domain = expression.AND(
                [
                    domain,
                    [
                        (
                            "vehicle_id",
                            "=",
                            self.vehicle_id.id if self.vehicle_id else False,
                        )
                    ],
                ]
            )
        if self.picking_type_id.batch_group_by_driver:
            domain = expression.AND(
                [
                    domain,
                    [
                        (
                            "driver_id",
                            "=",
                            self.driver_id.id if self.driver_id else False,
                        )
                    ],
                ]
            )
        return domain

    def _get_possible_batches_domain(self):
        domain = super()._get_possible_batches_domain()
        if self.picking_type_id.batch_group_by_vehicle:
            domain = expression.AND(
                [
                    domain,
                    [
                        (
                            "picking_ids.vehicle_id",
                            "=",
                            self.vehicle_id.id if self.vehicle_id else False,
                        )
                    ],
                ]
            )
        if self.picking_type_id.batch_group_by_driver:
            domain = expression.AND(
                [
                    domain,
                    [
                        (
                            "picking_ids.driver_id",
                            "=",
                            self.driver_id.id if self.vehicle_id else False,
                        )
                    ],
                ]
            )
        return domain

    def _get_auto_batch_description(self):
        description = super()._get_auto_batch_description()
        if self.picking_type_id.batch_group_by_vehicle and self.vehicle_id:
            description = (
                f"{description}, {self.vehicle_id.name}"
                if description
                else self.vehicle_id.name
            )
        if self.picking_type_id.batch_group_by_driver and self.driver_id:
            description = (
                f"{description}, {self.driver_id.name}"
                if description
                else self.driver_id.name
            )
        return description
