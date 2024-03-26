# Copyright 2020 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import models


class StockImmediateTransfer(models.TransientModel):
    _inherit = "stock.immediate.transfer"

    def process(self):
        # put context key for avoiding `base_delivery_carrier_label` auto-packaging feature
        return super(
            StockImmediateTransfer, self.with_context(set_default_package=False)
        ).process()
