# Copyright 2026 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class ChooseDeliveryCarrier(models.TransientModel):
    _inherit = "choose.delivery.carrier"

    def button_confirm(self):
        self = self.with_context(
            from_choose_delivery_carrier=True,
            choose_delivery_carrier_price=self.delivery_price,
        )
        return super().button_confirm()
