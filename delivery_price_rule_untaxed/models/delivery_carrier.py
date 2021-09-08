# Copyright 2018 Simone Rubino - Agile Business Group
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, models, _
from odoo.exceptions import UserError
from odoo.tools.safe_eval import safe_eval


class DeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'

    @api.multi
    def _get_price_available(self, order):
        self.ensure_one()
        self = self.with_context(
            {'order_amount_untaxed': order.amount_untaxed})
        res = super(DeliveryCarrier, self)._get_price_available(order)
        return res

    def _get_price_from_picking(self, total, weight, volume, quantity):
        price = 0.0
        untaxed_criteria_found = False
        price_dict = {
            'price': total,
            'volume': volume,
            'weight': weight,
            'wv': volume * weight,
            'quantity': quantity,
            'untaxed_price': self.env.context.get('order_amount_untaxed', 0)
        }
        untaxed_rule_present = False
        for line in self.price_rule_ids:
            test = safe_eval(
                line.variable + line.operator + str(line.max_value),
                price_dict)
            if line.is_untaxed_rule():
                untaxed_rule_present = True
                if test:
                    price = (line.list_base_price + line.list_price
                             * price_dict[line.variable_factor])
                    untaxed_criteria_found = True
                    break
            elif test:
                break

        if not untaxed_criteria_found:
            if untaxed_rule_present:
                # We cannot send everything to super if an untaxed rule
                # has failed because super doesn't know how to
                # handle untaxed_price variable
                raise UserError(_(
                    "Selected product in the delivery method doesn't "
                    "fulfill any of the delivery carrier(s) criteria."))
            return super(DeliveryCarrier, self) \
                ._get_price_from_picking(total, weight, volume, quantity)
        return price
