# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class StockQuantPackage(models.Model):
    _inherit = "stock.quant.package"

    number_of_parcels = fields.Integer(
        compute="_compute_number_of_parcels", store=True, readonly=False
    )

    @api.depends("package_type_id")
    def _compute_number_of_parcels(self):
        for rec in self:
            rec.number_of_parcels = rec.package_type_id.number_of_parcels
