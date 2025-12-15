# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class PackageType(models.Model):
    _inherit = "stock.package.type"

    number_of_parcels = fields.Integer("Number of parcels")
