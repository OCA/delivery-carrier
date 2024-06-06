# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models
from odoo.tools.safe_eval import safe_eval


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    collection_product_id = fields.Many2one(
        "product.product",
        domain="[('type', '=', 'service')]",
        string="Collection Product",
        ondelete="restrict",
        help="Fixed cost of collection, added as a separate product in the Sales Order",
    )
    collection_price = fields.Float(
        compute="_compute_collection_price",
        inverse="_inverse_product_collection_price",
        digits="Product Price",
        store=True,
        string="Collection Price",
    )

    @api.depends("product_id.list_price", "product_id.product_tmpl_id.list_price")
    def _compute_collection_price(self):
        for carrier in self:
            carrier.collection_price = carrier.collection_product_id.list_price

    def _inverse_product_collection_price(self):
        for carrier in self:
            carrier.collection_product_id.list_price = carrier.collection_price

    def _get_price_from_picking(self, total, weight, volume, quantity):
        """
        Solution to reuse as much of the original code as possible:
        if the variable is set,
        we rewrite the function to return the matching rule
        """
        if not self.env.context.get("get_delivery_rule"):
            return super()._get_price_from_picking(total, weight, volume, quantity)
        # Falsify variable in context
        self = self.with_context(get_delivery_rule=False)
        price_dict = self._get_price_dict(total, weight, volume, quantity)
        for line in self.price_rule_ids:
            test = safe_eval(
                line.variable + line.operator + str(line.max_value), price_dict
            )
            if test:
                return line
        return False

    def get_collection_price_unit(self, order):
        price = 0
        if self.collection_product_id:
            if self.delivery_type == "fixed":
                price = self.collection_price
            else:
                price_rule = self.with_context(
                    get_delivery_rule=True
                )._get_price_available(order)
                if price_rule:
                    price = price_rule.collection_price
        return price
