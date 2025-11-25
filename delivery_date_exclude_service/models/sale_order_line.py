# Copyright 2025 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def _expected_date(self):
        if (
            self.product_id
            and self.product_id.type == "service"
            and not self.product_id.service_affect_delivery_date
        ):
            return None
        return super()._expected_date()
