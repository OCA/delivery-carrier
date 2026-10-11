from odoo import fields, models


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    so_warehouse_id = fields.Many2one(
        comodel_name="stock.warehouse",
        string="Sales Order Warehouse",
        help="Default warehouse for the sales order that uses this delivery carrier",
    )
