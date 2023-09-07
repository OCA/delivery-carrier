# Copyright 2020 Tecnativa - David Vidal
# Copyright 2023 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    number_of_packages = fields.Integer(
        string="Number of Packages",
        compute="_compute_number_of_packages",
        readonly=False,
        store=True,
        default=0,
        copy=False,
    )

    @api.depends("package_ids")
    def _compute_number_of_packages(self):
        for picking in self:
            if picking.package_ids:
                picking.number_of_packages = len(picking.package_ids)
