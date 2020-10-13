from odoo import fields, models


class DeliveryCarrier(models.Model):
    """Extend to add delivery_category_id field."""

    _inherit = "delivery.carrier"

    delivery_category_id = fields.Many2one(
        "delivery.carrier.category", "Shipping Category"
    )


class DeliveryCarrierCategory(models.Model):
    """Model to manage carrier categories."""

    _name = "delivery.carrier.category"
    _description = "Delivery Carrier Category"

    name = fields.Char(required=True)
    description = fields.Text()
