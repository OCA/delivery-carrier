# Copyright 2022 Michael Tietz (MT Software) <mtietz@mt-software.de>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.tools import float_is_zero, groupby


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"
    
    def _is_delivered_method_delivery(self):
        res = super()._is_delivered_method_delivery()
        if res:
            return res
        return self._is_delivery() and self.product_id.type == "service"

    @api.depends("product_id", "is_delivery")
    def _compute_qty_delivered_method(self):
        super()._compute_qty_delivered_method()
