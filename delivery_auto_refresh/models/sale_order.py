# Copyright 2018 Tecnativa - Pedro M. Baeza
# Copyright 2021 Tecnativa - Carlos Roca
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.tools.safe_eval import safe_eval


class SaleOrder(models.Model):
    _inherit = "sale.order"

    carrier_id = fields.Many2one(
        compute="_compute_carrier_id", store=True, readonly=False
    )

    @api.depends("partner_id")
    def _compute_carrier_id(self):
        if hasattr(super(), "_compute_carrier_id"):
            super()._compute_carrier_id()
        for rec in self:
            if rec.partner_id:
                if rec.partner_id.property_delivery_carrier_id:
                    rec.carrier_id = rec.partner_id.property_delivery_carrier_id

    def _get_param_auto_add_delivery_line(self):
        get_param = self.env["ir.config_parameter"].sudo().get_param
        param = "delivery_auto_refresh.auto_add_delivery_line"
        return safe_eval(get_param(param, "0"))

    def _auto_refresh_delivery(self):
        self.ensure_one()
        # Make sure that if you have removed the carrier, the line is gone
        if self.state in {"draft", "sent"}:
            # Context added to avoid the recursive calls and save the new
            # value of carrier_id
            self.with_context(auto_refresh_delivery=True)._remove_delivery_line()
        if self._get_param_auto_add_delivery_line() and self.carrier_id:
            if self.state in {"draft", "sent"}:
                price_unit = self.carrier_id.rate_shipment(self)["price"]
                self._create_delivery_line(self.carrier_id, price_unit)
                self.with_context(auto_refresh_delivery=True).write(
                    {"recompute_delivery_price": False}
                )

    @api.model
    def create(self, vals):
        """Create or refresh delivery line on create."""
        order = super().create(vals)
        order._auto_refresh_delivery()
        return order

    def write(self, vals):
        """Create or refresh delivery line after saving."""
        res = super().write(vals)
        if self._get_param_auto_add_delivery_line() and not self.env.context.get(
            "auto_refresh_delivery"
        ):
            for order in self:
                delivery_line = order.order_line.filtered("is_delivery")
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

    def set_delivery_line(self, carrier, amount):
        if self._get_param_auto_add_delivery_line() and self.state in {"draft", "sent"}:
            self.carrier_id = carrier.id
        else:
            return super().set_delivery_line(carrier, amount)

    def _remove_delivery_line(self):
        current_carrier = self.carrier_id
        super()._remove_delivery_line()
        self.carrier_id = current_carrier
