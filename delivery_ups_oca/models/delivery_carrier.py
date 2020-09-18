# Copyright 2020 Hunki Enterprises BV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    delivery_type = fields.Selection(selection_add=[("ups", "UPS")],)

    def ups_send_shipping(self, pickings):
        return pickings._ups_send()

    def ups_get_tracking_link(self, picking):
        return picking._ups_tracking_url(
            len(picking.package_ids) <= 1 and
            picking.carrier_tracking_ref or
            '+'.join(picking.mapped('package_ids.parcel_tracking'))
        )

    def ups_cancel_shipment(self, pickings):
        return pickings._ups_cancel()
