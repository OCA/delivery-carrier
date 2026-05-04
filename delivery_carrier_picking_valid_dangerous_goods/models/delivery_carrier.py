# Copyright 2025 Camptocamp SA
# Copyright 2025 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
from odoo import fields, models
from odoo.exceptions import UserError


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    adr_limited_amount_ids = fields.Many2many(
        "adr.limited.amount",
        string="ADR limited amount",
        help="If a limited amount is defined here, this carrier will be "
        "excluded from the selection of carrier if any product has that same "
        "limited amount.",
    )

    def _match(self, partner, source):
        if source._name == "sale.order":
            products = source.order_line.product_id
        elif source._name == "stock.picking":
            # with_prefetch is needed to avoid a MemoryError on move product fetch
            # check https://github.com/OCA/OCB/commit/97919d6c28adc750d282a15f86320c576f3de872
            products = source.move_ids.with_prefetch().product_id
        else:
            raise UserError(self.env._("Invalid source document type"))
        return super()._match(partner, source) and self._match_dangerous_goods(products)

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
