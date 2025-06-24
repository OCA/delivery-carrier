# Copyright 2025 Tecnativa - Carlos Roca
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    # Introduce this extra dependency in the compute method to recalculate
    # the delivery price when the partner changes, since it depends on
    # the partner's address.
    @api.depends("partner_id")
    def _compute_delivery_price(self):
        return super()._compute_delivery_price()
