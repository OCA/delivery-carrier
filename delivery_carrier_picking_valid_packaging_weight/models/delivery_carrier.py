# Copyright 2025 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import models


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    def _match_picking_weight(self, picking):
        # Replace super behavior, use weight computed according to packaging
        self.ensure_one()
        picking.ensure_one()
        if not self.max_weight:
            return True
        return self.max_weight >= picking.estimated_shipping_weight
