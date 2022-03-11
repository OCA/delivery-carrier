# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    deposit_slip_id = fields.Many2one("deposit.slip", "Deposit Slip", copy=False)
