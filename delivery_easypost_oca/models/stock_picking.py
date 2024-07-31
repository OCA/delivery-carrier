from odoo import fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    easypost_oca_shipment_id = fields.Char()
    easypost_oca_rate_id = fields.Char()
    easypost_oca_carrier_name = fields.Char()
    easypost_oca_carrier_service = fields.Char()
    easypost_oca_carrier_id = fields.Char()
    easypost_oca_tracking_url = fields.Char()
