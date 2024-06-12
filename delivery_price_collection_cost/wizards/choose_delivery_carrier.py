# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class ChooseDeliveryCarrier(models.TransientModel):
    _inherit = "choose.delivery.carrier"

    collection_product_id = fields.Many2one(
        "product.product",
        related="carrier_id.collection_product_id",
    )
    collection_price = fields.Float(
        digits="Product Price", string="Collection Price", readonly=True
    )

    def _get_shipment_rate(self):
        res = super()._get_shipment_rate()
        if not res.get("error_message"):
            self.collection_price = self.carrier_id.get_collection_price_unit(
                self.order_id
            )
        return res
