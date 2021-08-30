# Copyright 2021 Camptocamp
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    is_delivery_extra = fields.Boolean(related="product_id.is_delivery_extra")

    def _is_delivery(self):
        return super()._is_delivery() or self._is_delivery_extra()

    def _is_delivery_extra(self):
        self.ensure_one()
        return self.is_delivery_extra
