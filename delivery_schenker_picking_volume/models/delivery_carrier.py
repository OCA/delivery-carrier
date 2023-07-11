# Copyright 2023 Michael Tietz (MT Software) <mtietz@mt-software.de>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import models


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    def _schenker_shipping_information_product_volume(self, product, qty):
        return product._get_volume_for_qty(qty)
