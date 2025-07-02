# Copyright 2025 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import models


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    def _match_picking(self, picking):
        self.ensure_one()
        picking.ensure_one()
        return (
            self._match_address(picking.partner_id)
            and self._match_picking_volume(picking)
            and self._match_picking_weight(picking)
        )

    def _match_picking_volume(self, picking):
        self.ensure_one()
        picking.ensure_one()
        if not self.max_volume:
            return True
        return self.max_volume >= picking.volume

    def _match_picking_weight(self, picking):
        self.ensure_one()
        picking.ensure_one()
        if not self.max_weight:
            return True
        return self.max_weight >= picking._get_estimated_weight()
