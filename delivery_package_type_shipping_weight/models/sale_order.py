from odoo import models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _get_estimated_weight(self):
        # Ignore product weight if specified in context.
        if self.env.context.get("ignore_product_weight"):
            return 0.0
        return super()._get_estimated_weight()
