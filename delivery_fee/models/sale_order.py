# Copyright 2026 Moduon
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _prepare_delivery_fee_line_vals(self, picking):
        # Based on core `_prepare_delivery_line_vals`
        carrier = picking.carrier_id
        context = {}
        if self.partner_id:
            # Set delivery detail in the customer language
            context["lang"] = self.partner_id.lang
            carrier = carrier.with_context(lang=self.partner_id.lang)
        # Apply fiscal position
        taxes = carrier.fee_product_id.taxes_id.filtered(
            lambda t: t.company_id.id == self.company_id.id
        )
        taxes_ids = taxes.ids
        if self.partner_id and self.fiscal_position_id:
            taxes_ids = self.fiscal_position_id.map_tax(taxes).ids
        # Create the sales order line
        so_description = (
            carrier.fee_product_id.description_sale
            or carrier.fee_product_id.display_name
        )
        so_description = f"{picking.name}: {so_description}"
        values = {
            "order_id": self.id,
            "name": so_description,
            "product_uom_qty": 1,
            "product_uom": carrier.fee_product_id.uom_id.id,
            "product_id": carrier.fee_product_id.id,
            "tax_id": [(6, 0, taxes_ids)],
            "price_unit": carrier.fee_product_id.list_price,
            "is_delivery_fee": True,
            "delivery_fee_picking_id": picking.id,
        }
        if self.order_line:
            values["sequence"] = self.order_line[-1].sequence + 1
        del context
        return values

    def _create_delivery_fee_line(self, picking):
        values = self._prepare_delivery_fee_line_vals(picking)
        return self.env["sale.order.line"].sudo().create(values)


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    is_delivery_fee = fields.Boolean(string="Is a Delivery Fee", default=False)
    delivery_fee_picking_id = fields.Many2one(comodel_name="stock.picking")

    def _is_not_sellable_line(self):
        return self.is_delivery_fee or super()._is_not_sellable_line()

    def _compute_pricelist_item_id(self):
        delivery_fee_lines = self.filtered("is_delivery_fee")
        res = super(
            SaleOrderLine, self - delivery_fee_lines
        )._compute_pricelist_item_id()
        delivery_fee_lines.pricelist_item_id = False
        return res

    @api.model_create_multi
    def create(self, vals_list):
        lines = super().create(vals_list)
        # Push fee lines to the bottom always
        # TODO: It'd be nice to have them in a section
        for order in lines.order_id:
            fee_lines = order.order_line.filtered("is_delivery_fee")
            last_sequence = order.order_line[-1].sequence
            for fee_line, increase in zip(fee_lines, range(1, len(fee_lines) + 1)):
                fee_line.sequence = last_sequence + increase
        return lines
