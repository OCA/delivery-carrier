# Copyright 2023 Michael Tietz (MT Software) <mtietz@mt-software.de>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import models


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    def _prepare_schenker_shipping(self, picking):
        vals = super()._prepare_schenker_shipping(picking)
        vals["shippingInformation"]["volume"] = picking.volume
        return vals
