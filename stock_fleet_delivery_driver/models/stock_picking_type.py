# Copyright 2025 Moduon Team S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)

from odoo import api, fields, models


class StockPickingType(models.Model):
    _inherit = "stock.picking.type"

    batch_group_by_vehicle = fields.Boolean(
        "Vehicle", help="Automatically group batches by vehicle"
    )
    batch_group_by_driver = fields.Boolean(
        "Driver", help="Automatically group batches by driver"
    )
    print_delivery_fleet_details = fields.Boolean(
        string="Print Vehicle and Driver on Delivery Slip",
        help="Print the vehicle license plate and delivery driver when available.",
    )

    @api.model
    def _get_batch_group_by_keys(self):
        return super()._get_batch_group_by_keys() + [
            "batch_group_by_vehicle",
            "batch_group_by_driver",
        ]
