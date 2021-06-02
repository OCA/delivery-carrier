# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging

from odoo import models

_logger = logging.getLogger(__name__)
try:
    from roulier import roulier
except ImportError:
    _logger.debug("Cannot `import roulier`.")


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
        if self._is_roulier():
            packages = picking._get_packages_from_picking()
            first_package = packages and packages[0]
            if first_package:
                return first_package._get_tracking_link(picking)
        else:
            return super().get_tracking_link(picking)
