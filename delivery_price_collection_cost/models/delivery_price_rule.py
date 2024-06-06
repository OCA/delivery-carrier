# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class DeliveryPriceRule(models.Model):
    _inherit = "delivery.price.rule"

    collection_price = fields.Float(digits="Product Price", string="Collection Price")

    @api.depends("collection_price", "carrier_id.collection_product_id")
    def _compute_name(self):
        res = super()._compute_name()
        for rule in self:
            if rule.carrier_id.collection_product_id:
                rule.name += " plus %(collection_price).02f collection price" % {
                    "collection_price": rule.collection_price
                }
        return res
