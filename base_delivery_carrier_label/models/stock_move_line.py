# Copyright 2016 Hpar
# Copyright 2016 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    weight = fields.Float(digits="Stock Weight", help="Weight of the pack_operation")

    def get_weight(self):
        """Calc and save weight of pack.operations.

        return:
            the sum of the weight of [self]
        """
        total_weight = 0
        for operation in self:
            product = operation.product_id

            # reserved_qty may be 0 if you don't set move line
            # individually but directly validate the picking
            qty = (
                operation.qty_done
                and operation.product_uom_id._compute_quantity(
                    operation.qty_done, operation.product_id.uom_id
                )
                or operation.reserved_qty
            )
            operation.weight = product.weight * qty

            total_weight += operation.weight
        return total_weight
