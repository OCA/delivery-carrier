# Copyright 2026 Yahia Sherif
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    bosta_tracking_timestamp = fields.Float(
        string="Bosta Status Time",
        readonly=True,
        copy=False,
        help="Bosta timeStamp of the last status applied, to ignore older updates.",
    )
    bosta_cod_amount = fields.Float(
        string="Bosta Cash on Delivery",
        readonly=True,
        copy=False,
        help="Amount Bosta was asked to collect for this transfer.",
    )
