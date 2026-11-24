# Copyright 2026 Nitrokey GmbH
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def _show_in_cart(self):
        self.ensure_one()
        return (
            super()._show_in_cart()
            and not self.is_ups_landed_cost
            and not self.is_ups_landed_cost_estimate
        )
