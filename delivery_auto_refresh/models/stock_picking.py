# Copyright 2018-2023 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def _add_delivery_cost_to_so(self):
        """Update delivery price in SO (no matter the type of carrier invoicing policy)
        and in picking from picking data if indicated so. Carriers based on rules
        doesn't refresh with real picking data, only with SO ones.
        """
        res = super()._add_delivery_cost_to_so()
        refresh_after_picking = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("delivery_auto_refresh.refresh_after_picking")
        )
        if not refresh_after_picking:
            return res
        self.ensure_one()
        sale_order = self.sale_id
        if not sale_order or not self.carrier_id:  # pragma: no cover
            return res
        so_line = sale_order.order_line.filtered(lambda x: x.is_delivery)[:1]
        if not so_line:  # pragma: no cover
            return res
        so_line = so_line.with_context(delivery_auto_refresh_override_locked=True)
        if self.carrier_id.delivery_type == "base_on_rule":
            total = weight = volume = quantity = 0
            for move_line in self.move_line_ids.filtered("qty_done"):
                if not move_line.product_id:
                    continue
                move = move_line.move_id
                qty = move.product_uom._compute_quantity(
                    move_line.qty_done,
                    move_line.product_id.uom_id,
                )
                weight += (move_line.product_id.weight or 0.0) * qty
                volume += (move_line.product_id.volume or 0.0) * qty
                quantity += qty
                total += move.sale_line_id.price_unit * qty
            total = sale_order.currency_id._convert(
                total,
                sale_order.company_id.currency_id,
                sale_order.company_id,
                sale_order.date_order,
            )
            self.carrier_price = self.carrier_id._get_price_from_picking(
                total,
                weight,
                volume,
                quantity,
            )
        if self.carrier_price and so_line.price_unit != self.carrier_price:
            so_line.with_context(
                delivery_auto_refresh_override_locked=True
            ).price_unit = self.carrier_price
        return res

    def _action_done(self):
        res = super()._action_done()
        # If configured, we want to set to 0 automatically the delivery line
        # when we have a returned picking that isn't invoiced so we don't have
        # it as invoiceable line. Otherwise, the salesman has to do it by hand.
        auto_void_delivery_line = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("delivery_auto_refresh.auto_void_delivery_line")
        )
        if not auto_void_delivery_line:
            return res
        sales_to_void_delivery = self.filtered(
            lambda x: x.sale_id
            and x.picking_type_code == "incoming"
            and x.sale_id._is_delivery_line_voidable()
        ).mapped("sale_id")
        sales_to_void_delivery.mapped("order_line").filtered(
            lambda x: x.is_delivery
        ).with_context(delivery_auto_refresh_override_locked=True).write(
            {"qty_delivered": 0, "product_uom_qty": 0, "price_unit": 0}
        )
        return res
