# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import json

from roulier import roulier

from odoo import models


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    def send_shipping(self, pickings):
        self.ensure_one()
        if self._is_roulier():
            return pickings._roulier_generate_labels()
        return super().send_shipping(pickings)

    def _is_roulier(self):
        self.ensure_one()
        available_carrier_actions = roulier.get_carriers_action_available() or {}
        return "get_label" in available_carrier_actions.get(self.delivery_type, [])

    def cancel_shipment(self, pickings):
        if self._is_roulier():
            pickings._cancel_shipment()
        else:
            return super().cancel_shipment(pickings)

    def get_tracking_link(self, picking):
        if not self._is_roulier():
            return super().get_tracking_link(picking)
        packages = picking.move_line_ids.result_package_id
        if not packages:
            return ""
        tracking_urls = []
        for package in packages:
            tracking_link = package._get_tracking_link()
            if tracking_link and tracking_link not in tracking_urls:
                tracking_urls.append(tracking_link)
        if not tracking_urls:
            return ""
        else:
            return (
                tracking_urls[0]
                if len(tracking_urls) == 1
                else json.dumps(tracking_urls)
            )

    def rate_shipment(self, order):
        res = super().rate_shipment(order)
        # for roulier carrier, usually getting the price by carrier webservice
        # is usually not available for now. Avoid failure in that case.
        if not res and self._is_roulier():
            res = {
                "success": True,
                "price": 0.0,
                "error_message": False,
                "warning_message": False,
            }
        return res
