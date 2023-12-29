from odoo import models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def get_return_label(self):
        self.ensure_one()
        tracking_number = None
        origin_date = None
        self.carrier_id.dhl_parcel_de_provider_get_return_label(
            self, tracking_number, origin_date
        )
