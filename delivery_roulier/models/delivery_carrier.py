# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from odoo import models

_logger = logging.getLogger(__name__)
try:
    from roulier import roulier
except ImportError:
    _logger.debug('Cannot `import roulier`.')


class DeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'

    # module using roulier don't use native method to get labels
    # pass False value to avoid failure.
    def send_shipping(self, pickings):
        res = super().send_shipping(pickings)
        if not res:
            return [{'exact_price': False, 'tracking_number': False}]
        return res

    def _is_roulier(self):
        self.ensure_one()
        return self.delivery_type in roulier.get_carriers()

    def cancel_shipment(self, pickings):
        if self._is_roulier:
            raise NotImplementedError()
        else:
            return super().cancel_shipment(pickings)

    # For now we keep our own roulier method _get_tracking_link instead of the
    # native one because the roulier logic is on packages when the Odoo logic
    # is on picking. An we could have multiple urls for 1 picking, if there
    # are multiple package...
    # Maybe we will merge all this in future versions
    def get_tracking_link(self, picking):
        if self._is_roulier:
            packages = picking._get_packages_from_picking()
            first_package = packages and packages[0]
            if first_package:
                return first_package._get_tracking_link(picking)
        else:
            return super().get_tracking_link()
