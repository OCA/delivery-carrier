# Copyright 2026 Tecnativa - Carlos Lopez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    max_quantity = fields.Float(
        help="If the total quantity of the order is over this quantity, "
        "the method won't be available.",
    )

    def _match_quantity(self, order):
        return (
            not self.max_quantity
            or sum(order_line.product_uom_qty for order_line in order.order_line)
            <= self.max_quantity
        )

    def _match(self, partner, order):
        return super()._match(partner, order) and self._match_quantity(order)
