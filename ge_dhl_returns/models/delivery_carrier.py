# Copyright 2021 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models
from .dhl_request import DhlRequest


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    def dhl_parcel_de_provider_get_return_label(
        self, picking, tracking_number, origin_date
    ):

        dhl_request = DhlRequest(self, picking)
        dhl_request.dhl_parcel_de_provider_get_return_label(
            picking, tracking_number, origin_date
        )

    def _compute_can_generate_return(self):  # pylint: disable=W8110
        super(DeliveryCarrier, self)._compute_can_generate_return()
        for carrier in self:
            if carrier.delivery_type == "dhl_parcel_de_provider":
                carrier.can_generate_return = True
