# Copyright 2018 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models
SKIP_REFRESH_DELIVERY = "skip_auto_refresh_delivery"


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def action_open_delivery_wizard(self):
        action = super().action_open_delivery_wizard()
        action.setdefault('context', {}).update({
            SKIP_REFRESH_DELIVERY: True
        })
        return action

    def _auto_refresh_delivery(self):
        """
        Simulate the wizard to update the price of delivery
        :return: bool
        """
        self.ensure_one()
        if self.env.context.get(SKIP_REFRESH_DELIVERY):
            return True
        action = self.with_context().action_open_delivery_wizard()
        wizard_model = action.get('res_model')
        wizard_ctx = action.get('context', {})
        wizard_obj = self.env[wizard_model].with_context(wizard_ctx)
        values = wizard_obj.default_get(wizard_obj.fields_get().keys())
        wizard = wizard_obj.create(values)
        wizard._get_shipment_rate()
        wizard.button_confirm()
        return True

    @api.model_create_multi
    def create(self, vals_list):
        """Create or refresh delivery line on create."""
        orders = super().create(vals_list)
        for order in orders:
            order._auto_refresh_delivery()
        return orders

    def write(self, vals):
        """Create or refresh delivery line after saving."""
        res = super().write(vals)
        for order in self:
            delivery_line = order.order_line.filtered("is_delivery")
            if len(delivery_line) > 1:
                continue
            order.with_context(
                delivery_discount=delivery_line.discount,
            )._auto_refresh_delivery()
        return res

    def _create_delivery_line(self, carrier, price_unit):
        """Allow users to keep discounts to delivery lines. Unit price will
           be recomputed anyway"""
        sol = super()._create_delivery_line(carrier, price_unit)
        discount = self.env.context.get("delivery_discount")
        if discount and sol:
            sol.discount = discount
        return sol
