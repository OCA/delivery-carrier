# Copyright 2020 Hunki Enterprises BV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class CarrierAccount(models.Model):
    _inherit = "carrier.account"

    ups_access_license = fields.Char("Access license number")
    ups_shipper_number = fields.Char("Shipper number")
    ups_negotiated_rates = fields.Boolean(
        help="""By default, shipping to UPS makes use of Published Rates. To
        use Negotiated Rates instead, just set this flag to True.
        A negotiated rate can be enabled only in case it's established by contract
        between your company and UPS.
    """)
