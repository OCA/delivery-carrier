#####################################################################################
# Copyright (c) 2023 Grüne Erde GmbH (https://grueneerde.com)
# All Right Reserved
#
# Licensed under the Odoo Proprietary License v1.0 (OPL).
# See LICENSE file for full licensing details.
#####################################################################################
from odoo import api, fields, models


class StockQuantPackage(models.Model):
    _inherit = "stock.quant.package"

    tracking_id = fields.Char()

    tracking_event_ids = fields.One2many(
        "tracking.event", "package_id", compute="_compute_tracking_event_ids"
    )

    delivery_state = fields.Char(compute="_compute_delivery_state", store=True)
    date_delivered = fields.Datetime(store=True)

    @api.depends("tracking_id")
    def _compute_tracking_event_ids(self):
        for record in self:
            tracking_event_ids = self.env["tracking.event"].search(
                [("piece_code", "=", record.tracking_id)]
            )
            record.tracking_event_ids = tracking_event_ids

    @api.depends("tracking_event_ids")
    def _compute_delivery_state(self):
        for record in self:
            if record.tracking_event_ids:
                for tracking_event_id in record.tracking_event_ids:
                    if "ZU" in tracking_event_id.standard_event_code:
                        record.delivery_state = "customer_delivered"
                        record.date_delivered = tracking_event_id.event_timestamp
                    else:
                        record.delivery_state = "in_transit"
            else:
                record.delivery_state = False
