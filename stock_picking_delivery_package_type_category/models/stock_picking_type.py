# Copyright 2024 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class StockPickingType(models.Model):

    _inherit = "stock.picking.type"

    authorized_package_type_cateogory_ids = fields.Many2many(
        comodel_name="stock.package.type.category",
        relation="stock_picking_type_package_type_category_rel",
        column1="package_type_id",
        column2="package_type_category_id",
        groups="stock.group_tracking_lot",
    )
