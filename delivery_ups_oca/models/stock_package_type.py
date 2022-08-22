# Copyright 2020 Hunki Enterprises BV
# Copyright 2022 Hibou Corp.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class StockPackageType(models.Model):
    _inherit = "stock.package.type"

    package_carrier_type = fields.Selection(selection_add=[("ups", "UPS")])
