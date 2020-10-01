# Copyright 2020 Hunki Enterprises BV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class CarrierAccount(models.Model):
    _inherit = "carrier.account"

    paazl_bearer_token = fields.Char(
        "Bearer token",
        help="Fill in the security token generated for the Paazl's push API",
    )
