# Copyright 2020 Camptocamp
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def _add_delivery_cost_to_so(self):
        res = super()._add_delivery_cost_to_so()
        self._add_package_fee_cost_to_so()
        return res

    def _add_package_fee_cost_to_so(self):
        if not self.carrier_id.package_fee_ids:
            return
        if not self.sale_id:
            return
        for package_fee in self.carrier_id.package_fee_ids:
            # Skip disabled fees (active_test is set to False by default on
            # the 'package_fee_ids' field)
            if package_fee.active:
                self.sale_id._create_package_fee_line(package_fee, self)
