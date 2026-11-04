# Copyright 2022 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    declared_value_currency_id = fields.Many2one(
        comodel_name="res.currency",
        string="Declared Value Currency",
        compute="_compute_declared_value_currency_id",
        store=True,
        readonly=True,
    )
    declared_value = fields.Monetary(
        currency_field="declared_value_currency_id",
        compute="_compute_declared_value",
        store=True,
        readonly=False,
        help="Declared value for shipping insurance.",
    )

    @api.depends(
        "sale_id", "sale_id.currency_id", "company_id", "company_id.currency_id"
    )
    def _compute_declared_value_currency_id(self):
        for picking in self:
            if picking.sale_id and picking.sale_id.currency_id:
                picking.declared_value_currency_id = picking.sale_id.currency_id
            else:
                picking.declared_value_currency_id = picking.company_id.currency_id

    def _get_declared_value_base_amount(self):
        self.ensure_one()
        if not self.sale_id:
            return 0.0
        total = 0.0
        for move in self.move_ids:
            sale_line = move.sale_line_id
            if not sale_line or not sale_line.product_uom_qty:
                continue
            unit_price = sale_line.price_total / sale_line.product_uom_qty
            total += unit_price * move.quantity
        return total

    @api.depends(
        "sale_id",
        "move_ids.quantity",
        "move_ids.sale_line_id.price_total",
        "move_ids.sale_line_id.product_uom_qty",
        "carrier_id",
    )
    def _compute_declared_value(self):
        for picking in self:
            picking.declared_value = picking._get_declared_value_base_amount() * (
                picking.carrier_id.declared_value_percentage / 100.0
            )

    def ups_get_label(self):
        self.ensure_one()
        tracking_ref = self.carrier_tracking_ref
        if self.delivery_type != "ups" or not tracking_ref:
            return
        return self.carrier_id.ups_get_label(tracking_ref)
