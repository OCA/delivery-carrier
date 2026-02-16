# Copyright 2026 Akretion (http://www.akretion.com).
# @author Florian Mounier <florian.mounier@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo import fields, models


class CarrierAccount(models.Model):
    _inherit = "carrier.account"

    dhl_express_account_number = fields.Char()
    dhl_express_file_format = fields.Selection(
        selection=[
            ("PDF", "PDF"),
            ("ZPL", "ZPL"),
            ("DPL", "LP2"),
            ("EPL", "EPL"),
        ],
        string="DHL Express File Format",
        help="Default format of the carrier's label you want to print",
    )
