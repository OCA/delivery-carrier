from odoo import models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def action_send_to_shipper_manually(self):
        self.ensure_one()
        # Do any additional manual send logic here if needed
        self.sudo().send_to_shipper()
        return True
