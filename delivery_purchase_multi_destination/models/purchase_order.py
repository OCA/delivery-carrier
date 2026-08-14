# Copyright 2025 Tecnativa - Carlos Roca
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    # Introduce these extra dependencies in the compute method to recalculate
    # the delivery price when the delivery address changes, since the matching
    # child carrier depends on it.
    @api.depends("partner_id", "dest_address_id")
    def _compute_delivery_price(self):
        return super()._compute_delivery_price()
