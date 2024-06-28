# Copyright 2020 Trey, Kilobytes de Soluciones
# Copyright 2020 FactorLibre
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    track_carrier_state = fields.Boolean(default=True)

    def send_shipping(self, pickings):
        res = super().send_shipping(pickings)
        pickings.write(
            {
                "date_shipped": fields.Date.today(),
                "delivery_state": "shipping_recorded_in_carrier"
                if self.track_carrier_state
                else "no_update",
            }
        )
        return res

    def cancel_shipment(self, pickings):
        super().cancel_shipment(pickings)
        pickings.write(
            {
                "delivery_state": "canceled_shipment",
                "date_delivered": False,
                "date_shipped": False,
            }
        )
