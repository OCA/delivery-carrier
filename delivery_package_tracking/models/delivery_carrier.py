# Copyright 2026 Jarsa
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo import fields, models


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    package_tracking_required = fields.Boolean(
        string="Tracking Reference per Package",
        help="Every package of a delivery shipped with this carrier needs its "
        "own tracking reference before the delivery is validated.",
    )

    def _get_package_tracking_link(self, tracking_ref):
        """Tracking page of one parcel, from the tracking link template of
        the carrier; carrier integrations may override it."""
        if not (self and tracking_ref and self.tracking_url):
            return False
        return self.tracking_url.replace("<shipmenttrackingnumber>", tracking_ref)
