# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)shipping_weight

from odoo import fields
from odoo.exceptions import ValidationError

from odoo.addons.base.tests.common import BaseCommon


class TestDeliveryPackageTypeShippingWeight(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.packaging = cls.env["stock.package.type"].create(
            {
                "name": "Delivery package A",
                "base_weight": 10.0,
                "is_base_weight_shipping_weight": True,
            }
        )
        cls.new_packaging = cls.env["stock.package.type"].create(
            {
                "name": "Delivery package B",
                "base_weight": 12.0,
                "is_base_weight_shipping_weight": True,
            }
        )
        cls.picking_type_out = cls.env.ref("stock.picking_type_out")
        cls.carrier = cls.env["delivery.carrier"].create(
            {
                "name": "Test Carrier",
                "delivery_type": "fixed",
                "product_id": cls.env["product.product"]
                .create({"name": "Local Delivery Testing"})
                .id,
            }
        )
        cls.product = cls.env["product.product"].create(
            {"name": "Test Weighted Product", "weight": 5.0, "is_storable": True}
        )
        cls.sale_order = cls.env["sale.order"].create(
            {
                "partner_id": cls.env.ref("base.res_partner_1").id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": cls.product.id,
                            "product_uom_qty": 1,
                        },
                    )
                ],
            }
        )
        cls.sale_order.action_confirm()

    def _get_package(self):
        """Helper to get a package from an assigned picking."""
        picking = self.env["stock.picking"].search(
            [
                ("picking_type_id", "=", self.picking_type_out.id),
                ("state", "=", "assigned"),
            ],
            limit=1,
        )
        move_line = fields.first(picking.move_line_ids_without_package)
        picking.action_put_in_pack()
        return move_line.result_package_id

    def test_check_negative_base_weight(self):
        """Ensure setting a negative base weight raises ValidationError."""
        with self.assertRaises(ValidationError):
            self.packaging.base_weight = -1

    def test_default_weight(self):
        """Verify shipping weight defaults to base weight when set via package type."""
        package = self._get_package()
        package.package_type_id = self.packaging
        self.quant = self.env["stock.quant"].create(
            {
                "location_id": self.env.ref("stock.stock_location_stock").id,
                "product_id": self.product.id,
                "quantity": 2,
                "package_id": package.id,
            }
        )
        package._compute_weight()
        self.assertAlmostEqual(package.weight, self.packaging.base_weight)

    def test_package_weight_when_base_weight_flag_disabled(self):
        """
        Ensure package weight includes quants weights if is_base_weight_shipping_weight
         is False.
        """
        self.packaging.is_base_weight_shipping_weight = False
        package = self._get_package()
        package.package_type_id = self.packaging
        self.quant = self.env["stock.quant"].create(
            {
                "location_id": self.env.ref("stock.stock_location_stock").id,
                "product_id": self.product.id,
                "quantity": 2,
                "package_id": package.id,
            }
        )
        package._compute_weight()
        # Expected weight = base_weight + (2 * 5.0)
        expected_weight = self.packaging.base_weight + (2 * self.product.weight)
        self.assertAlmostEqual(package.weight, expected_weight)

    def test_base_weight_shipping_weight_is_false(self):
        """
        If is_base_weight_shipping_weight is False, shipping weight should differ
        from base_weight.
        """
        self.packaging.is_base_weight_shipping_weight = False
        package = self._get_package()
        self.assertNotEqual(package.shipping_weight, self.packaging.base_weight)

    def test_onchange_sets_shipping_weight_from_package_type(self):
        """
        Test for `_onchange_package_type_id` correctly sets shipping weight from
        base weight.
        """
        package = self._get_package()
        package.shipping_weight = 0.0
        package.package_type_id = self.packaging
        package._onchange_package_type_id()
        self.assertAlmostEqual(
            package.shipping_weight,
            self.packaging.base_weight,
            msg="Shipping weight should be set from base_weight after onchange.",
        )

        package.package_type_id = self.new_packaging
        package._onchange_package_type_id()
        self.assertAlmostEqual(
            package.shipping_weight,
            self.new_packaging.base_weight,
            msg="Shipping weight should update when package_type_id changes.",
        )

    def test_package_weight_only_base_weight_if_flag_true(self):
        """
        Ensure that only base_weight is used for package weight when
        is_base_weight_shipping_weight is True
        """
        packages = self.carrier._get_packages_from_order(
            self.sale_order, self.packaging
        )
        self.assertEqual(len(packages), 1)
        self.assertEqual(packages[0].weight, self.packaging.base_weight)

    def test_package_weight_includes_product_weight_if_flag_false(self):
        """
        Ensure that both product weight and base_weight are used when
        is_base_weight_shipping_weight is False.
        """
        self.packaging.is_base_weight_shipping_weight = False
        packages = self.carrier._get_packages_from_order(
            self.sale_order, self.packaging
        )
        self.assertEqual(len(packages), 1)
        self.assertEqual(
            packages[0].weight, self.product.weight + self.packaging.base_weight
        )

    def test_shipping_weight_computation_in_pack_wizard(self):
        """
        Ensure the shipping weight in the 'choose.delivery.package' wizard
        is correctly computed using the package type's base weight.
        """
        self.env["stock.quant"]._update_available_quantity(
            self.product, self.env.ref("stock.stock_location_stock"), 2.0
        )
        picking = self.sale_order.picking_ids[0]
        picking.action_assign()
        picking.write({"carrier_id": self.carrier.id})
        pack_action = picking.action_put_in_pack()
        pack_action_ctx = pack_action["context"]
        pack_wizard = (
            self.env["choose.delivery.package"]
            .with_context(**pack_action_ctx)
            .create({"delivery_package_type_id": self.packaging.id})
        )
        pack_wizard._compute_shipping_weight()
        self.assertEqual(pack_wizard.shipping_weight, self.packaging.base_weight)
