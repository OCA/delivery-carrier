# Copyright 2025 Nitrokey GmbH
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class StockMove(models.Model):
    _inherit = "stock.move"

    sale_unit_price = fields.Float(
        string="Unit Price",
        digits="Product Price",
        compute="_compute_sale_unit_price",
        store=True,
        help="Unit price from the sale order line",
    )
    discount = fields.Float(
        string="Discount (%)",
        digits="Discount",
        compute="_compute_sale_unit_price",
        store=True,
        help="Discount from the sale order line",
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

    @api.depends("sale_line_id.price_unit", "sale_line_id.discount")
    def _compute_sale_unit_price(self):
        """Copy the price and discount from the sale order line"""
        for move in self:
            if move.sale_line_id:
                move.sale_unit_price = move.sale_line_id.price_unit
                move.discount = move.sale_line_id.discount
            else:
                move.sale_unit_price = move.product_id.lst_price
                move.discount = 0.0

    @api.depends("sale_unit_price", "product_uom_qty", "discount")
    def _compute_price_subtotal(self):
        """Compute the subtotal amount"""
        for move in self:
            price = move.sale_unit_price * (1 - (move.discount or 0.0) / 100.0)
            move.price_subtotal = price * move.product_uom_qty
