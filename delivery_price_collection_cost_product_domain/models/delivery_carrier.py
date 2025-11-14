# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import ast

from odoo import models
from odoo.tools.safe_eval import safe_eval


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    def _get_price_from_picking(self, total, weight, volume, quantity):
        """
        Solution to reuse as much of the original code as possible:
        if the variable is set,
        we rewrite the function from delivery_price_product_domain
        to return the matching rule
        """
        if not self.env.context.get("get_delivery_rule"):
            return super()._get_price_from_picking(total, weight, volume, quantity)
        price_dict = self._get_price_dict(total, weight, volume, quantity)
        untaxed_in_dict = "untaxed_price" in price_dict
        order = (
            self.env["sale.order"].sudo().browse(self._context.get("order_id", False))
        )
        for line in self.price_rule_ids:
            apply_product_domain_char = line.apply_product_domain
            if apply_product_domain_char and order:
                apply_product = order.order_line.product_id.search(
                    ast.literal_eval(apply_product_domain_char)
                )
                self.recompute_price_available(
                    apply_product, price_dict, untaxed_in_dict
                )
                test = safe_eval(
                    line.variable + line.operator + str(line.max_value), price_dict
                )
                if test:
                    self = self.with_context(get_delivery_rule=False)
                    return line

        return super()._get_price_from_picking(
            price_dict.get("price"),
            price_dict.get("weight"),
            price_dict.get("volume"),
            price_dict.get("quantity"),
        )
