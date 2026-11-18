# Copyright 2025 Tecnativa - Víctor Martínez
# Copyright 2026 Acysos S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def dachser_get_label(self):
        self.ensure_one()
        if self.delivery_type != "dachser" or not self.carrier_tracking_ref:
            return False
        return self.carrier_id.dachser_get_label(self)

    def dachser_send_to_tms(self):
        self.ensure_one()
        if self.delivery_type != "dachser":
            return False
        return self.carrier_id.dachser_send_order_to_tms(self)
