# Copyright 2019 Tecnativa - Victor M.M. Torres
# Copyright 2019-2020 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    number_of_packages = fields.Integer(string="Number of Packages", copy=False)

    def _determine_qty_field(self):
        self.ensure_one()
        field = "product_uom_qty"
        for opt_field in ["quantity_done", "reserved_availability"]:
            has = any(self.mapped("move_ids_without_package." + opt_field))
            if has:
                return opt_field
        return field

    @api.depends(
        "move_ids_without_package",
        "move_ids_without_package.product_id",
        "move_ids_without_package.product_uom_qty",
        "move_ids_without_package.quantity_done",
    )
    def _cal_weight(self):
        with_pack_ops = self.filtered("move_ids_without_package")
        for rec in self:
            field = rec._determine_qty_field()
            rec.weight = sum(
                rec.move_ids_without_package.mapped(
                    lambda x: x[field] * x.product_id.weight
                )
            )
        super(StockPicking, self - with_pack_ops)._cal_weight()

    def action_calculate_volume(self):
        for rec in self:
            field = rec._determine_qty_field()
            rec.volume = sum(
                rec.move_ids_without_package.mapped(
                    lambda x: x[field] * x.product_id.volume
                )
            )

    def _create_backorder(self):
        """Compute volume on newly created backorders."""
        backorders = super()._create_backorder()
        backorders.action_calculate_volume()
        return backorders
