# Copyright 2015 Serv. Tecnol. Avanzados - Pedro M. Baeza
# Copyright 2016 Tecnativa - Pedro M. Baeza
# Copyright 2023 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.tools.float_utils import float_is_zero


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    carrier_id = fields.Many2one(
        comodel_name="delivery.carrier",
        string="Delivery Method",
    )
    delivery_price = fields.Float(
        compute="_compute_delivery_price", store=True, readonly=False
    )

    @api.onchange("partner_id")
    def onchange_partner_id_delivery_purchase(self):
        if self.partner_id.property_delivery_carrier_id:
            self.carrier_id = self.partner_id.property_delivery_carrier_id.id

    @api.depends("order_line", "order_line.is_delivery", "amount_total", "carrier_id")
    def _compute_delivery_price(self):
        for item in self.filtered(lambda x: x.carrier_id):
            delivery_lines = item.order_line.filtered(lambda x: x.is_delivery)
            if delivery_lines:
                item.delivery_price = sum(delivery_lines.mapped("price_unit"))
            else:
                item.delivery_price = item.carrier_id.purchase_rate_shipment(self)[
                    "price"
                ]

    @api.model
    def _prepare_picking(self):
        res = super()._prepare_picking()
        if self.carrier_id:
            res["carrier_id"] = self.carrier_id.id
            res["carrier_price"] = self.delivery_price
        return res

    def _create_delivery_line(self, carrier, price_unit):
        pol_model = self.env["purchase.order.line"]
        line = pol_model.new(
            {
                "order_id": self.id,
                "product_qty": 1,
                "product_id": carrier.product_id.id,
                "is_delivery": True,
            }
        )
        line.onchange_product_id()
        values = line._convert_to_write(line._cache)
        # Override misc info: price_unit, name and sequence
        values.update(price_unit=price_unit)
        if carrier.free_over and self.currency_id.is_zero(price_unit):
            values["name"] += "\n" + _("Free Shipping")
        if self.order_line:
            values.update(sequence=self.order_line[-1].sequence + 1)
        return pol_model.sudo().create(values)


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    is_delivery = fields.Boolean(string="Is a Delivery", default=False)
    delivery_picking_orig_id = fields.Many2one(
        comodel_name="stock.picking", string="Origin picking (delivery)"
    )

    @api.depends("is_delivery")
    def _compute_qty_invoiced(self):
        """Overwrite and set qty_to_invoice to 0 for delivery lines if all lines
        have nothing to invoice."""
        precision = self.env["decimal.precision"].precision_get(
            "Product Unit of Measure"
        )
        res = super()._compute_qty_invoiced()
        for item in self.filtered(lambda x: x.is_delivery):
            order_lines = item.order_id.order_line.filtered(
                lambda x: not x.is_delivery and not x.display_type
            )
            if all(
                float_is_zero(line.qty_to_invoice, precision_digits=precision)
                for line in order_lines
            ):
                item.qty_to_invoice = 0
        return res
