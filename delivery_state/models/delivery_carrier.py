# Copyright 2020 Trey, Kilobytes de Soluciones
# Copyright 2020 FactorLibre
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class DeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'

    def send_shipping(self, pickings):
        res = super().send_shipping(pickings)
        pickings.write({
            'delivery_state': 'shipping_recorded_in_carrier',
            'date_shipped': fields.Date.today(),
        })
        return res

    def cancel_shipment(self, pickings):
        super().cancel_shipment(pickings)
        pickings.write({
            'delivery_state': 'canceled_shipment',
            'date_delivered': False,
            'date_shipped': False,
        })
