# Copyright 2022 Studio73 - Ethan Hildick <ethan@studio73.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models


class ChooseDeliveryCarrier(models.TransientModel):
    _inherit = "choose.delivery.carrier"

    @api.onchange("carrier_id")
    def _onchange_carrier_id(self):
        self.delivery_message = False
        if self.carrier_id.invoice_policy == "base_on_rule":
            vals = self._get_shipment_rate()
            if vals.get("error_message"):
                return {"error": vals["error_message"]}
        else:
            return super()._onchange_carrier_id()

    @api.onchange("order_id")
    def _onchange_order_id(self):
        # base_on_rule delivery price will be computed on each carrier change so
        # no need to recompute here
        if self.carrier_id.invoice_policy == "base_on_rule":
            return super()._onchange_order_id()
