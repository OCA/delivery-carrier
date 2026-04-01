# Copyright 2022 Impulso Diagonal - Javier Colmeiro
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class StockPackageType(models.Model):
    _inherit = "stock.package.type"

    package_carrier_type = fields.Selection(
        selection_add=[("sending", "Sending")],
        ondelete={"sending": "set default"},
    )
