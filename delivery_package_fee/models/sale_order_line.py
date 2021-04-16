# Copyright 2020 Camptocamp
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    package_fee_id = fields.Many2one(
        comodel_name="delivery.package.fee", default=False, ondelete="restrict"
    )

    def _is_delivery(self):
        return super()._is_delivery() or bool(self.package_fee_id)
