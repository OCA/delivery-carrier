# Copyright 2020 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    number_of_packages = fields.Integer(
        string="Number of Packages",
        compute="_compute_number_of_packages",
        readonly=False,
        store=True,
    )

    @api.depends("package_ids")
    def _compute_number_of_packages(self):
        for picking in self:
            picking.number_of_packages = len(picking.package_ids) or 1
