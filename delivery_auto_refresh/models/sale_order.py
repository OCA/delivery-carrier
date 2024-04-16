# Copyright 2018 Tecnativa - Pedro M. Baeza
# Copyright 2021 Tecnativa - Carlos Roca
# Copyright 2024 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models

from ..utils import get_bool_param


class SaleOrder(models.Model):
    _inherit = "sale.order"

    available_carrier_ids = fields.Many2many(
        comodel_name="delivery.carrier",
        compute="_compute_available_carrier_ids",
    )

    @api.onchange("partner_id", "partner_shipping_id")
    def _onchange_partner_id(self):
        if hasattr(super(), "_onchange_partner_id"):
            super()._onchange_partner_id()
        if get_bool_param(self.env, "set_default_carrier"):
            for order in self:
                action = order.action_open_delivery_wizard()
                carrier_id = self.env["delivery.carrier"].browse(
                    action["context"]["default_carrier_id"]
                )
                # If the carrier isn't allowed for the current shipping address, we wont
                # default to it. In that case we'd try to fallback to the former carrier.
                order.carrier_id = fields.first(
                    (carrier_id | order.carrier_id).filtered(
                        lambda x: x in order.available_carrier_ids._origin
                    )
                )

    @api.depends("partner_shipping_id")
    def _compute_available_carrier_ids(self):
        """We want to apply the same carriers filter in the header as in the wizard"""
        for sale in self:
            wizard = self.env["choose.delivery.carrier"].new({"order_id": sale.id})
            sale.available_carrier_ids = wizard.available_carrier_ids._origin

    def _get_param_auto_add_delivery_line(self):
        # When we have the context 'website_id' it means that we are doing the order from
        # e-commerce. So we don't want to add the delivery line automatically.
        if self.env.context.get("website_id"):
            return False
        return (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("delivery_auto_refresh.auto_add_delivery_line")
        )

    def _get_delivery_discount(self):
        self.ensure_one()
        delivery_lines = self.order_line.filtered("is_delivery")
        return delivery_lines[-1:].discount

    def _auto_refresh_delivery(self):
        self.ensure_one()
        if self.env.context.get("auto_refresh_delivery"):
            return
        if not self._get_param_auto_add_delivery_line():
            return

        delivery_discount = self._get_delivery_discount()

        # Make sure that if you have removed the carrier, the line is gone
        if self.state in {"draft", "sent"} and not self.env.context.get(
            "deleting_delivery_line"
        ):
            # Context added to avoid the recursive calls and save the new
            # value of carrier_id
            self.with_context(auto_refresh_delivery=True)._remove_delivery_line()
        if self.carrier_id:
            if self.state in {"draft", "sent"}:
                price_unit = self.carrier_id.rate_shipment(self)["price"]
                if not self.is_all_service:
                    sol = self._create_delivery_line(self.carrier_id, price_unit)
                    if delivery_discount and sol:
                        sol.discount = delivery_discount
                self.with_context(auto_refresh_delivery=True).write(
                    {"recompute_delivery_price": False}
                )

    @api.model_create_multi
    def create(self, vals_list):
        # Create or refresh delivery line on create
        orders = super().create(vals_list)
        for order in orders:
            order._auto_refresh_delivery()
        return orders

    def write(self, vals):
        # Prevent to refresh delivery in the call to super
        res = super(SaleOrder, self.with_context(auto_refresh_delivery=True)).write(
            vals
        )
        for order in self:
            order._auto_refresh_delivery()
        return res

    def set_delivery_line(self, carrier, amount):
        if self._get_param_auto_add_delivery_line() and self.state in {"draft", "sent"}:
            self.carrier_id = carrier.id
        else:
            return super().set_delivery_line(carrier, amount)

    def _remove_delivery_line(self):
        current_carrier = self.carrier_id
        super()._remove_delivery_line()
        self.carrier_id = current_carrier

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
        # Avoid locked orders validation error when voiding the delivery line
        fields = super()._get_protected_fields()
        if self.env.context.get("delivery_auto_refresh_override_locked"):
            return [x for x in fields if x not in ["product_uom_qty", "price_unit"]]
        return fields
