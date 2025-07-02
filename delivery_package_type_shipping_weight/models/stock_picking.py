from odoo import models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def _get_estimated_weight(self):
        # Ignore product weight if specified in context
        if self.env.context.get("ignore_product_weight"):
            return 0.0
        return super()._get_estimated_weight()
