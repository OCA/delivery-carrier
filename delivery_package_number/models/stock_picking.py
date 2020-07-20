# Copyright 2020 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    number_of_packages = fields.Integer(
        string="Number of Packages",
        default=1,
        copy=False,
    )


class StockPicking(models.Model):
    _inherit = "stock.move.line"

    @api.onchange("result_package_id")
    def onchange_package_ids(self):
        """TODO: in v13 Change field to compute readonly=False"""
        picking = self.picking_id
        picking.number_of_packages = len(picking.package_ids) or 1

    def write(self, vals):
        """TODO: in v13 Change field to compute readonly=False"""
        if "result_package_id" in vals:
            package_op = vals.get("result_package_id") and 1 or -1
            for picking in self.mapped("picking_id"):
                picking.number_of_packages += package_op
        return super().write(vals)
