# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResCompany(models.Model):

    _inherit = "res.company"

    automatic_package_creation_at_delivery_default = fields.Boolean(
        help="Check this if you want to have the automatic package creation configured"
        "for new delivery carriers."
    )
