# Copyright 2025 Tecnativa - Víctor Martínez
# Copyright 2026 Acysos S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class StockQuantPackage(models.Model):
    _inherit = "stock.quant.package"

    dachser_sscc = fields.Char(
        string="Dachser SSCC License Plate",
        copy=False,
        index=True,
        help=(
            "18-digit SSCC (NVE) license plate code assigned by Dachser "
            "to this package/pallet."
        ),
    )
