# Copyright 2023 Michael Tietz (MT Software) <mtietz@mt-software.de>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import models


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    def _schenker_shipping_information(self, picking):
        res = super()._schenker_shipping_information(picking)
        res["volume"] = picking.volume
        return res
