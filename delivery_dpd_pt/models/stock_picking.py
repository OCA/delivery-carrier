from odoo import fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    # Cash on delivery amount per shipment; enables DPD collect on delivery
    dpd_pt_cod_amount = fields.Float(
        string="COD Amount",
        help="Cash on delivery amount for DPD Portugal shipments, in euros",
    )
