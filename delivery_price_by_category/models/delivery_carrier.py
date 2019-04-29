# -*- coding: utf-8 -*-
# Copyright 2018 Simone Rubino - Agile Business Group
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, models
from odoo.tools import safe_eval


class DeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'

    @api.multi
    def get_price_available(self, order):
        self.ensure_one()
        category_price = 0.0
        price_dict = self.get_price_dict(order)
        for line in self.price_rule_ids:
            if line.product_category_id:
                products = order.mapped('order_line.product_id')
                test = any(product.categ_id == line.product_category_id
                           for product in products)
                if test:
                    category_price = line.product_category_price
                    break
            else:
                test = safe_eval(
                    line.variable + line.operator + str(line.max_value),
                    price_dict)
                if test:
                    break
        if category_price:
            return category_price

        # Note that this will evaluate all the price_rule_ids again and
        # our category rules might interfere withthe correct computation
        return super(DeliveryCarrier, self).get_price_available(order)

    def get_price_dict(self, order):
        weight = volume = quantity = 0
        total_delivery = 0.0
        for line in order.order_line:
            if line.state == 'cancel':
                continue
            if line.is_delivery:
                total_delivery += line.price_total
            if not line.product_id or line.is_delivery:
                continue
            qty = line.product_uom._compute_quantity(
                line.product_uom_qty, line.product_id.uom_id)
            weight += (line.product_id.weight or 0.0) * qty
            volume += (line.product_id.volume or 0.0) * qty
            quantity += qty
        total = (order.amount_total or 0.0) - total_delivery

        total = order.currency_id.with_context(date=order.date_order) \
            .compute(total, order.company_id.currency_id)
        return {'price': total, 'volume': volume, 'weight': weight,
                'wv': volume * weight, 'quantity': quantity}
