# Copyright 2021 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class ProductPackaging(models.Model):
    _inherit = "product.packaging"

    package_carrier_type = fields.Selection(selection_add=[("schenker", "DB Schenker")])
    schenker_stackable = fields.Boolean(
        string="Stackable", help="Define if the package is stackable by default"
    )
