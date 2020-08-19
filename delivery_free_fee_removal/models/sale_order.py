# Copyright 2019 Tecnativa - Vicent Cubells
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models
from odoo.tools.float_utils import float_is_zero


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _create_delivery_line(self, carrier, price_unit):
        rounding = self.currency_id.rounding
        if float_is_zero(price_unit, precision_rounding=rounding):
            return self.env["sale.order.line"]
        return super()._create_delivery_line(carrier, price_unit)
