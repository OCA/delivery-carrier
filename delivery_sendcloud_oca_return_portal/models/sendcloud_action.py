# Copyright 2026 arielbarreiros96 (https://github.com/arielbarreiros96)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl)

import json
import logging

from odoo import models

_logger = logging.getLogger(__name__)


class SendcloudAction(models.Model):
    _inherit = "sendcloud.action"

    def parse_result(self):
        self.ensure_one()
        try:
            message = json.loads(self.message)
        except (TypeError, ValueError):
            return super().parse_result()
        action = message.get("action") or ""
        if action.startswith("return"):
            return self._sendcloud_parse_return_action(message)
        res = super().parse_result()
        if action == "parcel_status_changed":
            self._sendcloud_parse_return_parcel(message)
        return res

    def _sendcloud_parse_return_action(self, message):
        self.ensure_one()
        return_data = message.get("return")
        if isinstance(return_data, dict):
            sendcloud_code = return_data.get("id")
        else:
            sendcloud_code = return_data or message.get("return_id")
        if not sendcloud_code:
            self.error_message = self.env._("No return identifier in the payload.")
            return False
        sendcloud_return = self.env["sendcloud.return"]._sendcloud_sync_return_code(
            sendcloud_code, self.company_id
        )
        if sendcloud_return:
            self._update_action_log(sendcloud_return)
        return True

    def _sendcloud_parse_return_parcel(self, message):
        """Create the Odoo return of a return parcel announced by webhook."""
        self.ensure_one()
        parcel_data = message.get("parcel") or {}
        if not parcel_data.get("is_return"):
            return False
        self.env["sendcloud.parcel"].sendcloud_create_update_parcels(
            [parcel_data], self.company_id.id
        )
        sendcloud_return = self.env["sendcloud.return"].search(
            [
                ("incoming_parcel_code", "=", parcel_data.get("id")),
                ("company_id", "=", self.company_id.id),
            ],
            limit=1,
        )
        if sendcloud_return:
            sendcloud_return._create_odoo_returns()
            self._update_action_log(sendcloud_return)
            return True
        _logger.info(
            "Sendcloud: return parcel %s is unknown, running a full return sync",
            parcel_data.get("id"),
        )
        self.env["sendcloud.return"].sendcloud_sync_returns()
        return True
