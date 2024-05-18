# Copyright 2024 Michael Tietz (MT Software) <mtietz@mt-software.de>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import models


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    def _schenker_shipping_information_package_volume(self, picking, package):
        return package.volume

    def _schenker_shipping_information_package(self, picking, package):
        res = super()._schenker_shipping_information_package(picking, package)
        res.update(
            {
                "length": self._schenker_shipping_information_round_dimension(
                    package.pack_length
                ),
                "width": self._schenker_shipping_information_round_dimension(
                    package.width
                ),
                "height": self._schenker_shipping_information_round_dimension(
                    package.height
                ),
            }
        )
        return res
