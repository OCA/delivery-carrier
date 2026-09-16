# Copyright 2026 arielbarreiros96 (https://github.com/arielbarreiros96)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl)

import logging

from odoo import api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _inherit = "stock.picking"

    sendcloud_return_ids = fields.One2many(
        "sendcloud.return", "picking_id", string="Sendcloud Return"
    )
    sendcloud_originated_return_ids = fields.One2many(
        "sendcloud.return", "original_picking_id", string="Sendcloud Returns"
    )

    def action_cancel(self):
        self._sendcloud_cancel_parcels()
        return super().action_cancel()

    def to_delete_sendcloud_pickings(self):
        if self.env.context.get("skip_sendcloud_cancel_sync"):
            return {}
        return super().to_delete_sendcloud_pickings()

    def _sendcloud_cancel_parcels(self):
        """Cancel the Sendcloud parcels of these transfers."""
        if self.env.context.get("skip_sendcloud_cancel_sync"):
            return
        for parcel in self.sendcloud_parcel_ids:
            parcel._sendcloud_cancel()

    @api.model
    def delete_sendcloud_pickings(self, to_delete_shipments):
        for integration_id, vals_list in to_delete_shipments.items():
            integration = self.env["sendcloud.integration"].browse(integration_id)
            for vals in vals_list:
                response = (
                    integration.delete_shipments(integration.sendcloud_code, vals) or {}
                )
                error = response.get("error") or {}
                if not error:
                    continue
                reference = vals.get("external_shipment_id") or vals.get(
                    "shipment_uuid"
                )
                if self._sendcloud_delete_shipment_is_absent(error):
                    _logger.info(
                        "Sendcloud: order %s was already gone, nothing to delete",
                        reference,
                    )
                    continue
                raise UserError(
                    self.env._(
                        "Sendcloud refused to delete the order of %(picking)s: "
                        "%(message)s\n\n"
                        "Cancel or delete it in Sendcloud first, then retry here.",
                        picking=reference,
                        message=error.get("message") or self.env._("no reason given"),
                    )
                )

    @api.model
    def _sendcloud_delete_shipment_is_absent(self, error):
        message = (error.get("message") or "").lower()
        return error.get("code") == 404 or "not found" in message

    def _sendcloud_return_portal_url(self):
        """URL of the Sendcloud return portal of this delivery, empty if it has none."""
        self.ensure_one()
        parcel = self.sendcloud_parcel_ids.filtered(lambda p: not p.is_return)[:1]
        if self.carrier_id.delivery_type != "sendcloud" or not parcel:
            return ""
        if parcel.return_portal_url in (False, "None"):
            try:
                parcel.action_get_return_portal_url()
            except UserError:
                _logger.exception(
                    "Sendcloud: could not fetch the return portal url of parcel %s",
                    parcel.sendcloud_code,
                )
                return ""
        url = parcel.return_portal_url
        return url if url and url != "None" else ""
