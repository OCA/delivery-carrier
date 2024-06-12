# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    is_delivery_collection = fields.Boolean(
        string="Is a Delivery Collection", default=False
    )

    def _check_line_unlink(self):
        """
        Lines that are delivery collection lines
        can be deleted from a confirmed order.
        """
        undeletable_lines = super()._check_line_unlink()
        return undeletable_lines.filtered(lambda line: not line.is_delivery_collection)
