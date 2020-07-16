# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models, fields


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    carrier_note = fields.Text(
        string='Sale carrier note',
        related='sale_id.carrier_note',
        store=False,
        readonly=True
    )