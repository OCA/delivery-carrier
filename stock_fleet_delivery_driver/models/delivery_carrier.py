# Copyright 2025 Moduon Team S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)

from odoo import api, fields, models


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    vehicle_id = fields.Many2one("fleet.vehicle", string="Vehicle")
    driver_id = fields.Many2one(
        compute="_compute_driver_id", store=True, readonly=False
    )

    @api.depends("vehicle_id")
    def _compute_driver_id(self):
        for record in self.filtered("vehicle_id"):
            record.driver_id = record.vehicle_id.driver_id
