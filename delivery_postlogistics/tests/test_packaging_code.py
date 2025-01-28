# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
from odoo.exceptions import UserError
from odoo.tests import Form

from .common import TestPostlogisticsCommon


class TestPackagingCode(TestPostlogisticsCommon):
    def test_shipper_package_default_code(self):
        # Case 0: Ensure the default codes are returned from the carrier
        self.assertEqual(
            self.carrier._postlogistics_get_default_custom_package_code(),
            self.postlogistics_default_package_type.shipper_package_code,
        )
        self.carrier.postlogistics_default_package_type_id = False
        self.assertEqual(
            self.carrier._postlogistics_get_default_custom_package_code(), "ECO"
        )

    def test_shipper_package_code_get_packaging_code_normal_return(self):
        # case 1: When package_carrier_type is set, shipper_package_code is
        # computed, and _get_shipper_package_code_list should return the expected codes
        package_type = self.postlogistics_default_package_type
        with Form(package_type) as type_form:
            type_form.package_carrier_type = self.carrier.delivery_type
        self.assertEqual(package_type._get_shipper_package_code_list(), ["ECO"])

    def test_shipper_package_code_get_packaging_code_empty_return(self):
        # Case 2: If no shipper_package_code is set on the package_type then
        # _get_shipper_package_code_list should return []
        package_type = self.postlogistics_default_package_type
        with Form(package_type) as type_form:
            type_form.package_carrier_type = False
        self.assertEqual(package_type._get_shipper_package_code_list(), [])

    def test_shipper_package_code_get_packaging_code_no_carrier_empty_return(self):
        # case 3: type is set, but no matching carrier is found
        # _get_shipper_package_code_list returns []
        package_type = self.postlogistics_default_package_type
        with Form(package_type) as type_form:
            type_form.package_carrier_type = "none"
        self.assertEqual(package_type._get_shipper_package_code_list(), [])

    def test_shipper_package_code_get_packaging_code_with_duplicates(self):
        # case 4: When shipper_package_code is set with duplicates, the
        # duplicates should be removed
        package_type = self.postlogistics_default_package_type
        with Form(package_type) as type_form:
            type_form.shipper_package_code = "PRI, PRI, BLN, VL, VL, BLN"
        self.assertEqual(
            package_type._get_shipper_package_code_list(deduplicate=False),
            ["BLN", "BLN", "PRI", "PRI", "VL", "VL"],
        )

    def test_shipper_package_code_get_packaging_code_remove_duplicates(self):
        # case 5: When shipper_package_code is set with duplicates, the
        # duplicates should be removed
        package_type = self.postlogistics_default_package_type
        with Form(package_type) as type_form:
            type_form.shipper_package_code = "PRI, PRI, BLN, VL, VL, BLN"
        self.assertEqual(
            package_type._get_shipper_package_code_list(), ["BLN", "PRI", "VL"]
        )

    def test_postlogistics_cancel_shipment(self):
        self.picking = self.env["stock.picking"].create(
            {
                "partner_id": self.env.ref("base.partner_demo").id,
                "picking_type_id": self.env.ref("stock.picking_type_out").id,
                "location_id": self.env.ref("stock.stock_location_stock").id,
                "location_dest_id": self.env.ref("stock.stock_location_customers").id,
            }
        )
        with self.assertRaises(UserError):
            self.carrier.postlogistics_cancel_shipment([self.picking])
