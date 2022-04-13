# Copyright 2018 Simone Rubino - Agile Business Group
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models
from odoo.tools.safe_eval import safe_eval


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    def _get_price_available(self, order):
        self.ensure_one()
        self = self.with_context({"order_amount_untaxed": order.amount_untaxed})
        return super(DeliveryCarrier, self)._get_price_available(order)

    def _get_price_from_picking(self, total, weight, volume, quantity):
        price = 0.0
        untaxed_criteria_found = False
        price_dict = {
            "price": total,
            "volume": volume,
            "weight": weight,
            "wv": volume * weight,
            "quantity": quantity,
            "untaxed_price": self.env.context.get("order_amount_untaxed", 0),
        }
        for line in self.price_rule_ids:
            test = safe_eval(
                line.variable + line.operator + str(line.max_value), price_dict
            )
            if line.is_untaxed_rule():
                if test:
                    price = (
                        line.list_base_price
                        + line.list_price * price_dict[line.variable_factor]
                    )
                    untaxed_criteria_found = True
                    break
            elif test:
                break

        if not untaxed_criteria_found:
            return super(DeliveryCarrier, self)._get_price_from_picking(
                total, weight, volume, quantity
            )
        return price

    def _get_price_dict(self, total, weight, volume, quantity):
        """Hook allowing to retrieve dict to be used in _get_price_from_picking() function.
        Hook to be overridden when we need to add some field to product
        and use it in variable factor from price rules."""
        res = super(DeliveryCarrier, self)._get_price_dict(
            total, weight, volume, quantity
        )
        res.update(
            {
                "untaxed_price": self.env.context.get("order_amount_untaxed", 0),
            }
        )
        return res
