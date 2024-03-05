# Copyright 2023 Ángel García de la Chica Herrera <angel.garcia@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class StockBackorderConfirmation(models.TransientModel):
    _inherit = "stock.backorder.confirmation"

    def process(self):
        # put context key for avoiding `base_delivery_carrier_label` auto-packaging feature
        return super(
            StockBackorderConfirmation, self.with_context(set_default_package=False)
        ).process()
