# Copyright 2025 Camptocamp SA
# Copyright 2025 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
from odoo import fields, models


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    adr_limited_amount_ids = fields.Many2many(
        "adr.limited.amount",
        string="ADR limited amount",
        help="If a limited amount is defined here, this carrier will be "
        "excluded from the selection of carrier if any product has that same "
        "limited amount.",
    )

    def _match(self, partner, order):
        return super()._match(partner, order) and self._match_dangerous_goods(
            order.order_line.product_id
        )

    def _match_picking(self, picking):
        return super()._match_picking(picking) and self._match_dangerous_goods(
            picking.move_ids.product_id
        )

    def _match_dangerous_goods(self, products):
        """Test products are compliants with dangerous goods"""
        if limited_amounts := self.adr_limited_amount_ids:
            for product in products:
                if product.adr_limited_amount_id in limited_amounts:
                    return False
        return True
