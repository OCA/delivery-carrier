# Copyright 2024 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import models


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    def send_shipping(self, pickings):
        # Shipping labels are attached to the record during this method. There's no
        # core hook method for this, and we want to avoid pulling a dependency in
        # every carrier implementation.
        previous_attachments = {
            picking: picking.allowed_shipping_attachement_ids for picking in pickings
        }
        result = super().send_shipping(pickings)
        for picking in pickings:
            picking.shipping_label_ids = (
                picking.allowed_shipping_attachement_ids - previous_attachments[picking]
            )
        return result
