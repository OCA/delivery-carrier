# Copyright 2025 Nitrokey GmbH
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    # Add computed fields to show the declared values of the picking
    amount_total = fields.Monetary(
        string="Total Value",
        compute="_compute_amount_total",
        store=True,
        help="Total value of the picking based on the values of the products",
    )
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        compute="_compute_currency_id",
        store=True,
        readonly=True,
    )
    declared_amount_percentage = fields.Float(
        string="Declared Amount (%)",
        default=100.0,
        help="Percentage of the sale price to be used as the declared value for shipping. "
        "100% means the full sale price will be used.",
    )
    declared_value = fields.Monetary(
        compute="_compute_declared_value",
        store=True,
        help="Declared value for shipping based on the total value and the declared percentage",
    )

    @api.depends(
        "sale_id", "sale_id.currency_id", "company_id", "company_id.currency_id"
    )
    def _compute_currency_id(self):
        """Get currency from sale order or company"""
        for picking in self:
            if picking.sale_id and picking.sale_id.currency_id:
                picking.currency_id = picking.sale_id.currency_id
            else:
                picking.currency_id = picking.company_id.currency_id

    @api.depends("sale_id", "amount_total", "declared_amount_percentage")
    def _compute_declared_value(self):
        """Compute the declared value based on total value and percentage"""
        for picking in self:
            if picking.sale_id:
                picking.declared_value = picking.amount_total * (
                    picking.declared_amount_percentage / 100.0
                )
            else:
                picking.declared_value = 0.0

    @api.onchange("carrier_id")
    def _onchange_carrier_id(self):
        """Update declared_amount_percentage when carrier changes"""
        if self.carrier_id:
            self.declared_amount_percentage = self.carrier_id.declared_amount_percentage

    @api.model
    def create(self, vals):
        """Set declared_amount_percentage from carrier on creation"""
        picking = super().create(vals)
        if picking.carrier_id:
            picking.declared_amount_percentage = (
                picking.carrier_id.declared_amount_percentage
            )
        return picking

    @api.depends("sale_id", "move_ids.price_subtotal")
    def _compute_amount_total(self):
        """Compute the total value of the picking"""
        for picking in self:
            if picking.sale_id:
                picking.amount_total = sum(picking.move_ids.mapped("price_subtotal"))
            else:
                picking.amount_total = 0.0
