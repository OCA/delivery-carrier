# Copyright 2020 Hunki Enterprises BV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class CarrierAccount(models.Model):
    _inherit = "carrier.account"

    ups_access_license = fields.Char("Access license number")
    ups_shipper_number = fields.Char("Shipper number")
