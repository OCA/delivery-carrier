# Copyright 2020 Trey, Kilobytes de Soluciones
# Copyright 2020 FactorLibre
# Copyright 2026 Raumschmiede GmbH
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models

from ..models.stock_picking import (
    DELIVERY_STATE_CANCELED,
    DELIVERY_STATE_NO_UPDATE,
    DELIVERY_STATE_SHIPPING_RECORDED,
)


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    track_carrier_state = fields.Boolean(default=True)
    days_fetch_tracking_state_update = fields.Integer(
        help="The tracking state is fetched for a picking for this number of days.\n"
        "If no final state has been set, the delivery state will be set to 'no_update'"
    )

    def send_shipping(self, pickings):
        res = super().send_shipping(pickings)
        pickings.write(
            {
                "date_shipped": fields.Date.today(),
                "delivery_state": DELIVERY_STATE_SHIPPING_RECORDED
                if self.track_carrier_state
                else DELIVERY_STATE_NO_UPDATE,
            }
        )
        return res

    def cancel_shipment(self, pickings):
        super().cancel_shipment(pickings)
        pickings.write(
            {
                "delivery_state": DELIVERY_STATE_CANCELED,
                "date_delivered": False,
                "date_shipped": False,
            }
        )
