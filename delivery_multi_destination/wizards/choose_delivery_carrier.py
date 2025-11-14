# SPDX-FileCopyrightText: 2024 Coop IT Easy SC
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from odoo import _, api, models


class ChooseDeliveryCarrier(models.TransientModel):
    _inherit = "choose.delivery.carrier"

    @api.onchange("carrier_id")
    def _onchange_carrier_id(self):
        result = super()._onchange_carrier_id()
        if self.delivery_type == "base_on_destination":
            vals = self._get_shipment_rate()
            # although ._onchange_carrier_id() in the delivery module can
            # return a dict with an "error" key and a string value, this is
            # not handled by the caller (see BaseModel._onchange_eval()),
            # which only handles dicts with a "warning" key and a dict as a
            # value.
            if vals.get("error_message"):
                return {
                    "warning": {"title": _("Error"), "message": vals["error_message"]}
                }
            if vals.get("warning_message"):
                return {"warning": {"message": vals["warning_message"]}}
        return result
