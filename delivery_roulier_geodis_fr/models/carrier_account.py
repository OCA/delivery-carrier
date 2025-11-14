# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class CarrierAccount(models.Model):
    _inherit = "carrier.account"

    geodis_fr_customer_id = fields.Char(string="Customer Id")
    geodis_fr_file_format = fields.Selection(
        [("ZPL", "ZPL")], default="ZPL", string="Geodis File Format"
    )
    geodis_fr_tracking_account = fields.Boolean(
        string="Is a Tracking Account",
        help="Check this box if this account is used to get the tracking links for geodis",
    )
