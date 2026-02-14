# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    nacex_with_return = fields.Boolean(
        string="With Return?",
        related="carrier_id.nacex_with_return",
        readonly=False,
        help="Enable return shipment for NACEX deliveries",
    )
