# Copyright 2024 Michael Tietz (MT Software) <mtietz@mt-software.de>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.addons.delivery_schenker.tests.common import TestDeliverySchenkerCommon


class TestDeliverySchenker(TestDeliverySchenkerCommon):
    def test_delivery_schenker(self):
        _sale_order, picking = self._create_sale_order()
        self._process_picking(picking, with_package=True)
        length = 14.0
        width = 13.0
        height = 12.0
        volume = length * width * height
        package = picking.package_ids
        package.pack_length = length
        package.width = width
        package.height = height
        expected_vals = self._prepare_schenker_shipping(picking)

        # Turn dimensions into str
        length = str(length) + "0"
        width = str(width) + "0"
        height = str(height) + "0"
        volume = str(volume) + "0"

        expected_vals["shippingInformation"]["shipmentPosition"][0].update(
            {
                "cargoDesc": " / ".join([picking.name, package.name]),
                "length": length,
                "width": width,
                "height": height,
                "volume": volume,
            }
        )
        expected_vals["shippingInformation"]["volume"] = volume
        expected_vals["measureUnitVolume"] = volume
        vals = self.carrier._prepare_schenker_shipping(picking)
        self.assertDictEqual(expected_vals, vals)
