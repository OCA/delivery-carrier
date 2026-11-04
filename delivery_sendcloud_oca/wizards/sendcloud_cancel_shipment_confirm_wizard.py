# Copyright 2024 Onestein (<https://www.onestein.nl>)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl)

from odoo import models


class SendcloudCancelShipmentConfirmWizard(models.TransientModel):
    _name = "sendcloud.cancel.shipment.confirm.wizard"
    _description = "Sendcloud Cancel Shipment Confirm Wizard"

    def do_cancel_shipment(self):
        active_id = self.env.context.get("active_id")
        if active_id and self.env.context.get("active_model") == "stock.picking":
            ctx = {
                "do_sendcloud_cancel_shipment": True,
                "skip_sync_picking_to_sendcloud": True,
            }
            picking = self.env["stock.picking"].browse(active_id)
            picking.with_context(**ctx).cancel_shipment()
