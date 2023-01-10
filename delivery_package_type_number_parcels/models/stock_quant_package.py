# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class StockQuantPackage(models.Model):
    _inherit = "stock.quant.package"

    number_of_parcels = fields.Integer(
        related="package_type_id.number_of_parcels",
        store=True,
    )
