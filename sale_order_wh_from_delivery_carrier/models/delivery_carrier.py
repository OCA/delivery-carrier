from odoo import fields, models


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    so_warehouse_id = fields.Many2one(
        comodel_name="stock.warehouse",
        string="SO Warehouse",
        help="Default Warehouse for sale where uses current Delivery Carrier",
    )
