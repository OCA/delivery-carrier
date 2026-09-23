from odoo import fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    # DPD Portugal specific field for COD amount per shipment
    dpd_portugal_cod_amount = fields.Float(
        string="COD Amount",
        help="Cash on delivery amount for DPD Portugal shipments",
    )
