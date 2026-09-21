# Copyright 2026 Akretion (http://www.akretion.com).
# @author Florian Mounier <florian.mounier@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _prepare_delivery_line_vals(self, carrier, price_unit):
        vals = super()._prepare_delivery_line_vals(carrier, price_unit)
        if self.company_id.free_over_as_discount and not price_unit:
            res = carrier.rate_shipment(self)

            # Check if the price unit is 0 due to a free over
            if (
                res["success"]
                and carrier.free_over
                and carrier.delivery_type != "base_on_rule"
                and carrier._compute_currency(
                    self,
                    self._compute_amount_total_without_delivery(),
                    "pricelist_to_company",
                )
                >= carrier.amount
            ):
                vals["price_unit"] = res["carrier_price"]
                vals["discount"] = 100.0
        return vals
