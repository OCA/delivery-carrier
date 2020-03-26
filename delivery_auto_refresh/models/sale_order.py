# Copyright 2018 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models
from odoo.tools import safe_eval


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _auto_refresh_delivery(self, force=False):
        self.ensure_one()
        # Avoid infinite recursion
        if self.env.context.get('force_delivery_set'):  # pragma: no cover
            return self
        get_param = self.env['ir.config_parameter'].sudo().get_param
        param = 'delivery_auto_refresh.auto_add_delivery_line'
        if (force or safe_eval(get_param(param, '0'))) and self.carrier_id:
            if (self.state in {'draft', 'sent'} or
                    self.invoice_shipping_on_delivery):
                self.with_context(force_delivery_set=True).set_delivery_line()

    def write(self, vals):
        """Refresh delivery price after saving."""
        vals.update({'delivery_rating_success': True})
        res = super(SaleOrder, self).write(vals)
        for order in self:
            delivery_line = order.order_line.filtered('is_delivery')
            # Make sure that if you have removed the carrier, the line is gone
            discount = delivery_line.discount
            if order.state in {'draft', 'sent'}:
                order._remove_delivery_line()
            order.with_context(
                delivery_discount=discount
                )._auto_refresh_delivery(force=bool(delivery_line))
        return res

    def _create_delivery_line(self, carrier, price_unit):
        """Allow users to keep discounts to delivery lines. Unit price will
           be recomputed anyway"""
        sol = super()._create_delivery_line(carrier, price_unit)
        discount = self.env.context.get('delivery_discount')
        if discount and sol:
            sol.discount = discount
        return sol
