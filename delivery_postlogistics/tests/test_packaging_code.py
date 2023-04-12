# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo.tests.common import Form, TransactionCase

PACKAGE_CODE = "blah-biddy, bloo-blah, blah-blah-biddy, bloo-blah"
EXPECTED_CODES = ["blah-biddy", "bloo-blah", "blah-blah-biddy", "bloo-blah"]


class TestPackagingCode(TransactionCase):
    at_install = False
    post_install = True

    @classmethod
    def setUpClass(cls):
        super(TestPackagingCode, cls).setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.carrier = cls.env.ref("delivery.delivery_carrier")
        cls.carrier.delivery_type = "postlogistics"
        cls.package_type = cls.env["stock.package.type"].create(
            {
                "name": "Packaging Test",
                "package_carrier_type": "postlogistics",
                "shipper_package_code": "PRI, BLN",
            }
        )

    def test_shipper_package_code_get_packaging_code(self):
        # If no shipper_package_code is set on the package_type then
        # _get_packaging_codes should return []
        with Form(self.package_type) as package_type:
            package_type.package_carrier_type = False
        self.assertEqual(self.package_type._get_packaging_codes(), [])
        # case 2: type is set, but no matching carrier is found
        # _get_packaging_codes returns []
        with Form(self.package_type) as package_type:
            package_type.package_carrier_type = "none"
        self.assertEqual(self.package_type._get_packaging_codes(), [])
        # case 3: When package_carrier_type is set, shipper_package_code is
        # computed, and _get_packaging_codes should return the expected codes
        with Form(self.package_type) as package_type:
            package_type.package_carrier_type = self.carrier.delivery_type
            package_type.shipper_package_code = PACKAGE_CODE
        self.assertEqual(self.package_type._get_packaging_codes(), EXPECTED_CODES)
