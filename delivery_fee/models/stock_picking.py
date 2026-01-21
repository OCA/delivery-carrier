# Copyright 2026 Moduon
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
from odoo import models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def _add_delivery_cost_to_so(self):
        res = super()._add_delivery_cost_to_so()
        self._add_delivery_fee_to_order()
        return res

    def _add_delivery_fee_to_order(self):
        if (
            not self.sale_id
            or self.partner_id.delivery_fee_exemption
            or not self.carrier_id.fee_product_id
        ):
            return
        self.sale_id._create_delivery_fee_line(self)
