# Copyright 2018 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models
from odoo.tools import safe_eval


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _auto_refresh_delivery(self):
        self.ensure_one()
        # Make sure that if you have removed the carrier, the line is gone
        if self.state in {'draft', 'sent'}:
            self._remove_delivery_line()
        get_param = self.env['ir.config_parameter'].sudo().get_param
        param = 'delivery_auto_refresh.auto_add_delivery_line'
        if safe_eval(get_param(param, '0')) and self.carrier_id:
            if (self.state in {'draft', 'sent'} or
                    self.invoice_shipping_on_delivery):
                price_unit = self.carrier_id.rate_shipment(self)['price']
                self._create_delivery_line(self.carrier_id, price_unit)

    @api.model
    def create(self, vals):
        """Create or refresh delivery line on create."""
        order = super().create(vals)
        order._auto_refresh_delivery()
        return order

    def write(self, vals):
        """Create or refresh delivery line after saving."""
        res = super(SaleOrder, self).write(vals)
        for order in self:
            delivery_line = order.order_line.filtered('is_delivery')
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
        discount = self.env.context.get('delivery_discount')
        if discount and sol:
            sol.discount = discount
        return sol

    def _is_delivery_line_voidable(self):
        """If the picking is returned before being invoiced, like when the picking
        is delivered but immediately return because the customer refused the order,
        so no delivery charges should be applied."""
        # There are invoiceable lines so there's no full return or the lines
        # were not set to refund.
        qty_delivered = sum(
            self.order_line.filtered(
                lambda x: not x.is_delivery and x.product_id.type != "service"
            ).mapped("qty_delivered")
        )
        # There must be validated pickings
        pickings = self.picking_ids.filtered(lambda x: x.state == "done")
        # If there aren't delivery lines or the order is a quotation there's
        # nothing to be done either. If there are more than one delivery lines
        # we won't be doing anything as well.
        if (
            self.state not in {"done", "sale"}
            or self.invoice_ids
            or not self.order_line.filtered("is_delivery")
            or len(self.order_line.filtered("is_delivery")) > 1
            or qty_delivered
            or not pickings
        ):
            return False
        return True


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def _get_protected_fields(self):
        """Avoid locked orders validation error when voiding the
        delivery line"""
        fields = super()._get_protected_fields()
        if self.env.context.get("delivery_auto_refresh_override_locked"):
            return [
                x for x in fields if x not in ["product_uom_qty", "price_unit"]
            ]
        return fields
