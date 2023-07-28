# Copyright 2023 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo.exceptions import ValidationError
from odoo.tests.common import SavepointCase


class TestCarrierBarcodePattern(SavepointCase):
    at_install = False
    post_install = True

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.setUpClassCarrier()

    @classmethod
    def setUpClassCarrier(cls):
        cls.carrier_without_pattern = cls.env.ref("delivery.delivery_carrier")
        cls.carrier_with_pattern = cls.env.ref("delivery.normal_delivery_carrier")
        cls.carrier_with_pattern.return_barcode_pattern = "PREFIX(?P<origin>.*)"
        cls.carrier_model = cls.env["delivery.carrier"]

    def test_valid_regex(self):
        error_msg = "Return Barcode Pattern must be a valid regular expression"
        with self.assertRaisesRegex(ValidationError, error_msg):
            self.carrier_with_pattern.return_barcode_pattern = "[.*"
        self.carrier_with_pattern.return_barcode_pattern = "[0-9]+(?P<origin>.*)"

    def test_parse_barcodes(self):
        so_name = "SO12345"
        barcode = f"PREFIX{so_name}"
        # PREFIX(.*) doesn't match SO12345, an empty set will be returned.
        self.assertEqual(
            [],
            self.carrier_model._get_origin_from_barcode(so_name),
        )
        # PREFIX(.*) matches PREFIXSO12345, both the barcode and SO12345
        # will be returned
        self.assertEqual(
            [so_name], self.carrier_model._get_origin_from_barcode(barcode)
        )
