# Copyright 2025 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
from odoo import fields, models


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    adr_limited_amount_ids = fields.Many2many(
        "limited.amount",
        string="Restrict selection of preferred carrier for ADR limited amount",
        help="If a limited amount is defined here, this carrier will be "
        "excluded from the selection of preferred carrier on stock picking if "
        "said picking contains any move with products that define the same "
        "limited amount.",
    )

    def _match_picking(self, picking):
        return super()._match_picking(picking) and self._match_dangerous_goods(picking)

    def _match_dangerous_goods(self, picking):
        # Returns True if picking is compliant with carrier regarding limited
        # amounts of dangerous goods
        if limited_amounts := self.adr_limited_amount_ids:
            for product in picking.move_ids.product_id:
                if product.limited_amount_id in limited_amounts:
                    return False
        return True
