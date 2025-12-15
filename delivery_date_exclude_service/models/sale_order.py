# Copyright 2025 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _select_expected_date(self, expected_dates):
        expected_dates = [date for date in expected_dates if date]
        if not expected_dates:
            return None
        return super()._select_expected_date(expected_dates)
