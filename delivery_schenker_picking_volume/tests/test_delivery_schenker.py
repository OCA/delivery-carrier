# Copyright 2023 Michael Tietz (MT Software) <mtietz@mt-software.de>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.addons.delivery_schenker.tests.common import TestDeliverySchenkerCommon


class TestDeliverySchenker(TestDeliverySchenkerCommon):
    def test_delivery_schenker(self):
        """This result should be the same as in delivery_schenker
        because the overridden mehtod _schenker_shipping_information_product_volume
        should return the same as it is in the main module
        """
        vals = self.carrier._prepare_schenker_shipping(self.picking)
        self.assertDictEqual(self._prepare_schenker_shipping(self.picking), vals)
