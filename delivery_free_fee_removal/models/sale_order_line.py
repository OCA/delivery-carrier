# Copyright 2020 Camptocamp
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    is_free_delivery = fields.Boolean(compute="_compute_is_free_delivery", store=True)

    @api.depends("is_delivery", "currency_id", "price_total")
    def _compute_is_free_delivery(self):
        for line in self:
            line.is_free_delivery = line.is_delivery and line.currency_id.is_zero(
                line.price_total
            )

    def _compute_invoice_status(self):
        # Override the standard invoice status computation to mark free delivery
        # lines as invoiced after the order confirmation, avoiding them being
        # considered pending invoicing since they do not require a separate
        # invoice line.
        free_delivery_lines = self.filtered(
            lambda line: line.order_id.state == "sale" and line.is_free_delivery
        )
        res = super()._compute_invoice_status()
        for line in free_delivery_lines:
            line.invoice_status = "invoiced"
        return res

    def _compute_qty_to_invoice(self):
        # Free delivery lines should never have quantities pending to invoice
        # because they do not generate invoiceable amounts.
        free_delivery_lines = self.filtered(
            lambda line: line.order_id.state == "sale" and line.is_free_delivery
        )
        res = super()._compute_qty_to_invoice()
        for line in free_delivery_lines:
            line.qty_to_invoice = 0
        return res
