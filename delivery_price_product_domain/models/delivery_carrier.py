# Copyright 2023 Cetmix OÜ - Andrey Solodovnikov
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import ast

from odoo import fields, models
from odoo.tools.safe_eval import safe_eval


class DeliveryPriceRule(models.Model):
    _inherit = "delivery.carrier"

    order_id = fields.Many2one("sale.order", string="Sale Order")

    def recompute_price_available(self, apply_product, price_dict, untaxed_in_dict):
        """This method recompute total parameters only with apply products"""
        self.ensure_one()
        self_sudo = self.sudo()
        order = self_sudo.order_id
        total = weight = volume = quantity = 0
        total_delivery = 0.0
        untaxed_amount = order.amount_untaxed
        for line in order.order_line:
            qty = line.product_uom._compute_quantity(
                line.product_uom_qty, line.product_id.uom_id
            )
            if line.state == "cancel" or line.product_id not in apply_product:
                total -= (line.price_total or 0.0) * qty
                if untaxed_in_dict:
                    untaxed_amount -= (line.price_unit or 0.0) * qty
                continue
            if line.is_delivery:
                total_delivery += line.price_total
            if (not line.product_id or line.is_delivery) and (
                line.product_id.type == "service"
            ):
                continue
            weight += (line.product_id.weight or 0.0) * qty
            volume += (line.product_id.volume or 0.0) * qty
            quantity += qty
        total += (order.amount_total or 0.0) - total_delivery

        total = self_sudo._compute_currency(order, total, "pricelist_to_company")
        price_dict.update(
            price=total,
            weight=weight,
            volume=volume,
            quantity=quantity,
            untaxed_price=untaxed_amount,
        )
        return self_sudo._get_price_dict(total, weight, volume, quantity)

    def _get_price_from_picking(self, total, weight, volume, quantity):
        "Find price rule matching SO base on apply_product_domain"
        if self.free_over and total >= self.amount:
            return 0
        price_dict = self._get_price_dict(total, weight, volume, quantity)
        untaxed_in_dict = "untaxed_price" in price_dict
        test = False
        rule_line = self.price_rule_ids[0]
        for line in self.price_rule_ids:
            apply_product_domain_char = line.apply_product_domain
            if apply_product_domain_char and self.order_id:
                apply_product = self.order_id.order_line.product_id.search(
                    ast.literal_eval(apply_product_domain_char)
                )
                self.recompute_price_available(
                    apply_product, price_dict, untaxed_in_dict
                )
                test = safe_eval(
                    line.variable + line.operator + str(line.max_value), price_dict
                )
                if test:
                    rule_line = line
                    break

        if test and untaxed_in_dict:
            return (
                rule_line.list_base_price
                + rule_line.list_price * price_dict[rule_line.variable_factor]
            )

        return super(DeliveryPriceRule, self)._get_price_from_picking(
            price_dict.get("price"),
            price_dict.get("weight"),
            price_dict.get("volume"),
            price_dict.get("quantity"),
        )

    def _get_price_available(self, order):
        "Compute price, weight, quantity, volume of SO"
        self.order_id = order
        return super(DeliveryPriceRule, self)._get_price_available(order)
