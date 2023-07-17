# Copyright 2023 Michael Tietz (MT Software) <mtietz@mt-software.de>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from .common import TestDeliverySchenkerCommon


class TestDeliverySchenker(TestDeliverySchenkerCommon):
    def test_delivery_schenker(self):
        vals = self.carrier._prepare_schenker_shipping(self.picking)
        self.assertDictEqual(self._prepare_schenker_shipping(self.picking), vals)

    def test_delivery_schenker_address_number(self):
        vals = self.carrier._prepare_schenker_shipping(self.picking)
        self.assertEqual(
            list(filter(lambda a: a["type"] == "SHIPPER", vals["address"]))[0][
                "schenkerAddressId"
            ],
            self.carrier.schenker_address_number,
        )
        self.carrier.schenker_partner_invoice_id = self.company.partner_id.id
        vals = self.carrier._prepare_schenker_shipping(self.picking)
        self.assertEqual(
            list(filter(lambda a: a["type"] == "INVOICE", vals["address"]))[0][
                "schenkerAddressId"
            ],
            self.carrier.schenker_address_number,
        )
        self.assertTrue(
            "schenkerAddressId"
            not in list(filter(lambda a: a["type"] == "SHIPPER", vals["address"]))[0]
        )
