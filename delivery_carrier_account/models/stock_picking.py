# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


from odoo import models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    # All carrier module implementation should use this method in order to get the
    # carrier account, instead of doing directly "picking.carrier_id.carrier_account_id"
    # this way, it leaves the possibility to override globally (for all carriers)
    # the way to get the carrier account.
    # For instance, if a case requires to have multiple carrier account per delivery
    # method, using a method leaves the possibility to implements the multiple
    # account logic and make it work for all carrier modules installed.
    def _get_carrier_account(self):
        self.ensure_one()
        return self.carrier_id.carrier_account_id
