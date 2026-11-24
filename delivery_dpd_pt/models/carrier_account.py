# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class CarrierAccount(models.Model):
    _inherit = "carrier.account"

    dpd_pt_client_id = fields.Char(
        string="DPD OAuth Client ID",
        help="Client ID of the DPD Portugal API application.",
    )
    dpd_pt_client_secret = fields.Char(
        string="DPD OAuth Client Secret",
        groups="base.group_system",
        help="Client secret of the DPD Portugal API application.",
    )
