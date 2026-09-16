# Copyright 2026 arielbarreiros96 (https://github.com/arielbarreiros96)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl)

import logging
from datetime import timedelta

from odoo import SUPERUSER_ID, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

SENDCLOUD_CANCELLED_STATUSES = ("1998", "2000")
SENDCLOUD_CANCELLATION_DAYS = 14


class SendcloudParcel(models.Model):
    _inherit = "sendcloud.parcel"

    def write(self, vals):
        res = super().write(vals)
        if {"tracking_number", "shipment", "picking_id"} & set(vals):
            self._sendcloud_sync_return_picking()
        if "sendcloud_status" in vals:
            self._sendcloud_apply_cancellation()
        return res

    def _sendcloud_sync_return_picking(self):
        """Copy the shipping method and tracking number onto the return operation."""
        for parcel in self:
            picking = parcel.picking_id
            if not picking or picking.picking_type_id.code != "incoming":
                continue
            vals = {}
            if parcel.shipment_id and not picking.carrier_id:
                vals["carrier_id"] = parcel.shipment_id.id
            if parcel.tracking_number and not picking.carrier_tracking_ref:
                vals["carrier_tracking_ref"] = parcel.tracking_number
            if vals:
                picking.with_context(skip_sync_picking_to_sendcloud=True).write(vals)

    def _sendcloud_is_cancelled(self):
        return bool(self) and self[:1].sendcloud_status in SENDCLOUD_CANCELLED_STATUSES

    def _sendcloud_cancel(self):
        """Cancel this parcel at Sendcloud, raising when Sendcloud refuses."""
        self.ensure_one()
        if self._sendcloud_is_cancelled():
            return True
        integration = self.company_id.sendcloud_default_integration_id
        if not integration:
            return False
        response = integration.cancel_parcel(self.sendcloud_code) or {}
        if not self._sendcloud_cancel_accepted(response):
            raise UserError(
                self.env._(
                    "Sendcloud refused to cancel parcel %(parcel)s: %(message)s\n\n"
                    "Cancel or delete it in Sendcloud first, then retry here.",
                    parcel=self.sendcloud_code,
                    message=self._sendcloud_cancel_message(response),
                )
            )
        self.with_context(skip_sendcloud_cancel_picking=True).sendcloud_status = "2000"
        return True

    @api.model
    def _sendcloud_cancel_accepted(self, response):
        if response.get("status") in ("cancelled", "deleted", "queued"):
            return True
        message = response.get("message") or ""
        if response.get("status") == "failed" and "already being cancelled" in message:
            return True
        return (response.get("error") or {}).get("code") == 404

    @api.model
    def _sendcloud_cancel_message(self, response):
        error = response.get("error") or {}
        return (
            error.get("message")
            or response.get("message")
            or self.env._("no reason given")
        )

    def _sendcloud_apply_cancellation(self):
        """Cancel the transfers of the parcels cancelled at Sendcloud."""
        if self.env.context.get("skip_sendcloud_cancel_picking"):
            return
        for parcel in self:
            picking = parcel.picking_id
            if not picking or not parcel._sendcloud_is_cancelled():
                continue
            if picking.state == "cancel":
                continue
            if picking.state == "done":
                parcel._sendcloud_schedule_warning(
                    self.env._(
                        "Sendcloud cancelled parcel %(parcel)s, but this transfer is "
                        "already done and cannot be cancelled here.",
                        parcel=parcel.sendcloud_code,
                    )
                )
                continue
            picking_su = picking.with_user(SUPERUSER_ID)
            picking_su.with_context(skip_sendcloud_cancel_sync=True).action_cancel()
            picking_su.message_post(
                body=self.env._(
                    "Cancelled because Sendcloud cancelled parcel %(parcel)s.",
                    parcel=parcel.sendcloud_code,
                )
            )

    def _sendcloud_schedule_warning(self, note):
        self.ensure_one()
        picking = self.picking_id
        picking.with_user(SUPERUSER_ID).activity_schedule(
            "mail.mail_activity_data_warning",
            user_id=picking.user_id.id or SUPERUSER_ID,
            note=note,
        )

    def _sendcloud_has_open_warning(self):
        self.ensure_one()
        return any(
            str(self.sendcloud_code) in str(activity.note or "")
            for activity in self.picking_id.activity_ids
        )

    @api.model
    def sendcloud_check_cancelled_parcels(self):
        """Verify with Sendcloud the cancellations it has had the time to complete."""
        deadline = fields.Datetime.now() - timedelta(days=SENDCLOUD_CANCELLATION_DAYS)
        domain = [
            ("picking_id.state", "=", "cancel"),
            ("sendcloud_status", "not in", SENDCLOUD_CANCELLED_STATUSES),
            ("write_date", "<", deadline),
        ]
        for parcel in self.search(domain):
            integration = parcel.company_id.sendcloud_default_integration_id
            if not integration or parcel._sendcloud_has_open_warning():
                continue
            try:
                parcel_data = integration.get_parcel(parcel.sendcloud_code)
            except UserError:
                _logger.warning(
                    "Sendcloud: could not refresh parcel %s", parcel.sendcloud_code
                )
                continue
            if not parcel_data:
                continue
            self.sendcloud_create_update_parcels([parcel_data], parcel.company_id.id)
            if parcel._sendcloud_is_cancelled():
                continue
            parcel._sendcloud_schedule_warning(
                self.env._(
                    "Sendcloud still reports parcel %(parcel)s as not cancelled, so "
                    "its label may still be active. Check it in Sendcloud.",
                    parcel=parcel.sendcloud_code,
                )
            )
