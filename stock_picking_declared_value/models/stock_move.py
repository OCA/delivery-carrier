# Copyright 2025 Nitrokey GmbH
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class StockMove(models.Model):
    _inherit = "stock.move"

    sale_unit_price = fields.Float(
        string="Sales Unit Price",
        digits="Product Price",
        compute="_compute_sale_unit_price",
        store=True,
        help="Net unit price from the sale order line (including discount)",
    )
    price_subtotal = fields.Monetary(
        string="Subtotal",
        compute="_compute_price_subtotal",
        store=True,
        help="Subtotal amount for the move line",
    )
    currency_id = fields.Many2one(
        related="picking_id.currency_id",
        string="Currency",
        readonly=True,
    )

    @api.depends("sale_line_id", "sale_line_id.price_reduce_taxexcl")
    def _compute_sale_unit_price(self):
        """Copy the net price (including discount) from the sale order line"""
        for move in self:
            if move.sale_line_id:
                move.sale_unit_price = move.sale_line_id.price_reduce_taxexcl
            else:
                move.sale_unit_price = 0.0

    @api.depends("sale_line_id", "sale_unit_price", "product_uom_qty")
    def _compute_price_subtotal(self):
        """Compute the subtotal amount"""
        for move in self:
            if move.sale_line_id:
                move.price_subtotal = move.sale_unit_price * move.product_uom_qty
            else:
                move.price_subtotal = 0.0
