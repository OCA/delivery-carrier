import ast

from odoo import models
from odoo.tools.safe_eval import safe_eval
from odoo.exceptions import UserError

class DeliveryPriceRule(models.Model):
    _inherit = "delivery.carrier"

    def recompute_price_available(self, order, exclude_product):
        '''This method recompute total parameters of order without exclude products'''
        self.ensure_one()
        self = self.sudo()
        total = weight = volume = quantity = 0
        total_delivery = 0.0
        for line in order.order_line:
            qty = line.product_uom._compute_quantity(line.product_uom_qty, line.product_id.uom_id)
            if line.state == 'cancel' or line.product_id in exclude_product:
                total -= (line.product_id.list_price or 0.0) * qty
                continue
            if line.is_delivery:
                total_delivery += line.price_total
            if not line.product_id or line.is_delivery:
                continue
            if line.product_id.type == "service":
                continue
            weight += (line.product_id.weight or 0.0) * qty
            volume += (line.product_id.volume or 0.0) * qty
            quantity += qty
        total += (order.amount_total or 0.0) - total_delivery

        total = self._compute_currency(order, total, 'pricelist_to_company')
        price_dict = self._get_price_dict(total, weight, volume, quantity)
        return price_dict

    def _get_price_available(self, order):
        self.ensure_one()
        self = self.sudo()
        order = order.sudo()
        total = weight = volume = quantity = 0
        total_delivery = 0.0
        for line in order.order_line:
            if line.state == 'cancel':
                continue
            if line.is_delivery:
                total_delivery += line.price_total
            if not line.product_id or line.is_delivery:
                continue
            if line.product_id.type == "service":
                continue
            qty = line.product_uom._compute_quantity(line.product_uom_qty, line.product_id.uom_id)
            weight += (line.product_id.weight or 0.0) * qty
            volume += (line.product_id.volume or 0.0) * qty
            quantity += qty
        total = (order.amount_total or 0.0) - total_delivery

        total = self._compute_currency(order, total, 'pricelist_to_company')

        return self._get_price_from_picking(total, weight, volume, quantity, order.order_line)
    
    def _get_price_from_picking(self, total, weight, volume, quantity, order_line):
        price_dict = self._get_price_dict(total, weight, volume, quantity)
        if self.free_over and total >= self.amount:
            return 0
        for line in self.price_rule_ids:
            test = safe_eval(line.variable + line.operator + str(line.max_value), price_dict)
            if test:
                exclude_product_domain_char = line.exclude_product_domain
                if (exclude_product_domain_char):
                    exclude_product = order_line.product_id.search(ast.literal_eval(exclude_product_domain_char))
                    price_dict = self.recompute_price_available(order_line.order_id, exclude_product)
                break
        
        return super(DeliveryPriceRule, self)._get_price_from_picking(price_dict.get('price'),
                                                                      price_dict.get('weight'),
                                                                      price_dict.get('volume'),
                                                                      price_dict.get('quantity'))
    