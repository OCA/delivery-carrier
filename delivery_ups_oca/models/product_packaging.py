# Copyright 2020 Hunki Enterprises BV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class ProductPackaging(models.Model):
    _inherit = "product.packaging"

    package_carrier_type = fields.Selection(
        selection=[("none", "None"), ("ups", "UPS")],
        string="Carrier",
        default="none",
    )
    shipper_package_code = fields.Char()
