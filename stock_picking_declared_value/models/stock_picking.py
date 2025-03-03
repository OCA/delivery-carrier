# Copyright 2025 Nitrokey GmbH
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    # Add a computed field to show the total declared value of the picking
    amount_total = fields.Monetary(
        string="Total Declared Value",
        compute="_compute_amount_total",
        store=True,
        help="Total declared value of the picking based on the values of the products",
    )
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        related="sale_id.currency_id",
        readonly=True,
    )
    declared_amount = fields.Float(
        string="Declared Amount (%)",
        default=100.0,
        help="Percentage of the sale price to be used as the declared value for shipping. "
        "100% means the full sale price will be used.",
    )

    @api.onchange("carrier_id")
    def _onchange_carrier_id(self):
        """Update declared_amount when carrier changes"""
        if self.carrier_id and self.carrier_id.declared_amount:
            self.declared_amount = self.carrier_id.declared_amount

    @api.model
    def create(self, vals):
        """Set declared_amount from carrier on creation"""
        picking = super().create(vals)
        if picking.carrier_id and picking.carrier_id.declared_amount:
            picking.declared_amount = picking.carrier_id.declared_amount
        return picking

    @api.depends("move_lines.price_subtotal", "declared_amount")
    def _compute_amount_total(self):
        """Compute the total declared value of the picking"""
        for picking in self:
            subtotal = sum(picking.move_lines.mapped("price_subtotal"))
            picking.amount_total = subtotal * (picking.declared_amount / 100.0)
