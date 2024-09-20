# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from roulier import roulier

from odoo import models


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    def alternative_send_shipping(self, pickings):
        self.ensure_one()
        if self._is_roulier():
            return pickings._roulier_generate_labels()
        else:
            return super().alternative_send_shipping(pickings)

    def _is_roulier(self):
        self.ensure_one()
        available_carrier_actions = roulier.get_carriers_action_available() or {}
        return "get_label" in available_carrier_actions.get(self.delivery_type, [])

    def cancel_shipment(self, pickings):
        if self._is_roulier:
            pickings._cancel_shipment()
        else:
            return super().cancel_shipment(pickings)

    # For now we keep our own roulier method _get_tracking_link instead of the
    # native one because the roulier logic is on packages when the Odoo logic
    # is on picking. An we could have multiple urls for 1 picking, if there
    # are multiple package...
    # Maybe we will merge all this in future versions
    def get_tracking_link(self, picking):
        if not self._is_roulier():
            return super().get_tracking_link(picking)
        packages = picking.package_ids
        if not packages:
            return ""
        first_package = packages[0]
        return first_package._get_tracking_link()

    def rate_shipment(self, order):
        res = super().rate_shipment(order)
        # for roulier carrier, usually getting the price by carrier webservice
        # is usually not available for now. Avoid failure in that case.
        if not res and self.is_roulier():
            res = {
                "success": True,
                "price": 0.0,
                "error_message": False,
                "warning_message": False,
            }
        return res
