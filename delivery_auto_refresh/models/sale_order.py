# Copyright 2018 Tecnativa - Pedro M. Baeza
# Copyright 2021 Tecnativa - Carlos Roca
# Copyright 2024 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    available_carrier_ids = fields.Many2many(
        comodel_name="delivery.carrier",
        compute="_compute_available_carrier_ids",
    )

    @api.depends("partner_shipping_id")
    def _compute_available_carrier_ids(self):
        """We want to apply the same carriers filter in the header as in the wizard"""
        for sale in self:
            wizard = self.env["choose.delivery.carrier"].new({"order_id": sale.id})
            sale.available_carrier_ids = wizard.available_carrier_ids._origin

    def _set_delivery_carrier(self, set_delivery_line=True):
        for order in self:
            delivery_wiz_action = order.action_open_delivery_wizard()
            delivery_wiz_context = delivery_wiz_action.get("context", {})
            if not delivery_wiz_context.get("default_carrier_id"):
                continue
            delivery_wiz = (
                self.env[delivery_wiz_action.get("res_model")]
                .with_context(**delivery_wiz_context)
                .new({})
            )

            # Do not override carrier
            if order.carrier_id:
                delivery_wiz.carrier_id = order.carrier_id

            # If the carrier isn't allowed, we won't default to it
            if (
                delivery_wiz.carrier_id
                not in delivery_wiz.available_carrier_ids._origin
            ):
                continue

            if not set_delivery_line or order.is_all_service:
                # Only set the carrier
                if order.carrier_id != delivery_wiz.carrier_id:
                    order.carrier_id = delivery_wiz.carrier_id
            else:
                delivery_wiz._get_shipment_rate()
                delivery_wiz.button_confirm()

    @api.onchange("partner_id", "partner_shipping_id")
    def _add_delivery_carrier_on_partner_change(self):
        partner = self.partner_shipping_id or self.partner_id
        if not partner:
            return
        if self.company_id.sale_auto_assign_carrier_on_create:
            self._set_delivery_carrier(set_delivery_line=False)

    def _is_auto_set_carrier_on_create(self):
        self.ensure_one()
        if self.state not in ("draft", "sent"):
            return False
        return self.company_id.sale_auto_assign_carrier_on_create

    def _is_auto_add_delivery_line(self):
        # When we have the context 'website_id' it means that we are doing the order from
        # e-commerce. So we don't want to add the delivery line automatically.
        if self.env.context.get("website_id"):
            return False
        return self.company_id.sale_auto_add_delivery_line

    # Part of Odoo. See LICENSE file for full copyright and licensing details.
    def _prepare_delivery_line_vals(self, carrier, price_unit):
        context = {}
        if self.partner_id:
            # set delivery detail in the customer language
            context["lang"] = self.partner_id.lang
            carrier = carrier.with_context(lang=self.partner_id.lang)

        # Apply fiscal position
        taxes = carrier.product_id.taxes_id.filtered(
            lambda t: t.company_id.id == self.company_id.id
        )
        taxes_ids = taxes.ids
        if self.partner_id and self.fiscal_position_id:
            taxes_ids = self.fiscal_position_id.map_tax(taxes).ids

        # Create the sales order line

        if carrier.product_id.description_sale:
            so_description = "%s: %s" % (
                carrier.name,
                carrier.product_id.description_sale,
            )
        else:
            so_description = carrier.name
        values = {
            "order_id": self.id,
            "name": so_description,
            "product_uom_qty": 1,
            "product_uom": carrier.product_id.uom_id.id,
            "product_id": carrier.product_id.id,
            "tax_id": [(6, 0, taxes_ids)],
            "is_delivery": True,
        }
        if carrier.invoice_policy == "real":
            values["price_unit"] = 0
            values["name"] += _(
                " (Estimated Cost: %s )", self._format_currency_amount(price_unit)
            )
        else:
            values["price_unit"] = price_unit
        if carrier.free_over and self.currency_id.is_zero(price_unit):
            values["name"] += "\n" + _("Free Shipping")
        if self.order_line:
            values["sequence"] = self.order_line[-1].sequence + 1
        del context
        return values

    # end of the odoo part

    def _update_delivery_line(self, delivery_line, price_unit):
        """Update the existing delivery line"""
        values = self._prepare_delivery_line_vals(self.carrier_id, price_unit)
        new_vals = {}
        for f, val in values.items():
            field_def = delivery_line._fields.get(f)
            if isinstance(field_def, (fields.One2many, fields.Many2many)):
                # Tax is set with a SET command
                clear = update = False
                for cmd in val:
                    if cmd[0] == 6:
                        if delivery_line[f].ids != cmd[2]:
                            update = True
                    else:
                        clear = True
                if clear:
                    new_vals[f] = [(5, 0, 0)] + val
                elif update:
                    new_vals[f] = val
            elif isinstance(field_def, fields.Many2one):
                if delivery_line[f].id != val:
                    new_vals[f] = val
            elif f == "sequence":
                # sequence is last sequence + 1. As the delivery line already
                # exists, substract 1
                if delivery_line[f] != val - 1:
                    new_vals[f] = val
            elif delivery_line[f] != val:
                new_vals[f] = val
        if new_vals:
            delivery_line.write(new_vals)

    def _auto_refresh_delivery(self):
        self.ensure_one()
        if (
            self.env.context.get("auto_refresh_delivery")
            or not self._is_auto_add_delivery_line()
            or self.state not in ("draft", "sent")
        ):
            return

        self = self.with_context(auto_refresh_delivery=True)

        if not self.carrier_id:
            self._set_delivery_carrier()

        if not self.carrier_id or self.is_all_service:
            self._remove_delivery_line()
        else:
            price_unit = self.carrier_id.rate_shipment(self)["price"]
            delivery_lines = self.order_line.filtered("is_delivery")
            if not delivery_lines:
                self._create_delivery_line(self.carrier_id, price_unit)
            elif len(delivery_lines) > 1:
                delivery_discount = delivery_lines[-1:].discount
                self._remove_delivery_line()
                sol = self._create_delivery_line(self.carrier_id, price_unit)
                if delivery_discount and sol:
                    sol.discount = delivery_discount
            else:
                self._update_delivery_line(delivery_lines[0], price_unit)
        if self.recompute_delivery_price:
            self.recompute_delivery_price = False

    @api.model_create_multi
    def create(self, vals_list):
        # Prevent to refresh delivery in the call to super
        orders = (
            super(SaleOrder, self.with_context(auto_refresh_delivery=True))
            .create(vals_list)
            .with_context(auto_refresh_delivery=False)
        )
        for order in orders:
            if not order.carrier_id and order._is_auto_set_carrier_on_create():
                order._set_delivery_carrier()
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
        if self._is_auto_add_delivery_line() and self.state in ("draft", "sent"):
            # This will trigger an _auto_refresh_delivery in write
            self.carrier_id = carrier.id
        else:
            return super().set_delivery_line(carrier, amount)

    def _is_delivery_line_voidable(self):
        """If the picking is returned before being invoiced, like when the picking
        is delivered but immediately return because the customer refused the order,
        so no delivery charges should be applied."""
        self.ensure_one()
        if not self.company_id.sale_auto_void_delivery_line:
            return False

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
            self.state not in ("done", "sale")
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

    @api.model_create_multi
    def create(self, vals_list):
        lines = super(
            SaleOrderLine, self.with_context(auto_refresh_delivery=True)
        ).create(vals_list)
        for order in lines.order_id:
            order._auto_refresh_delivery()
        return lines

    def write(self, vals):
        res = super(SaleOrderLine, self.with_context(auto_refresh_delivery=True)).write(
            vals
        )
        for order in self.order_id:
            order._auto_refresh_delivery()
        return res
