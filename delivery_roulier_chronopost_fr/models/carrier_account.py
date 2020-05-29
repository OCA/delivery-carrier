# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class CarrierAccount(models.Model):
    _inherit = 'carrier.account'

    chronopost_fr_subaccount = fields.Char("Chronopost Sub Account", size=3)
    chronopost_fr_file_format = fields.Selection(
        selection=[('PDF', 'PDF'), ('PPR', 'PPR'), ('SPD', 'SPD'),
                   ('THE', 'THE'), ('SER', 'SER'), ('Z2D', 'Z2D'),
                   ('XML', 'XML'), ('THEPSG', 'THEPSG'), ('Z2DPSG', 'Z2DPSG')],
        string='Chronopost File Format',
        help="Default format of the carrier's label you want to print"
    )
