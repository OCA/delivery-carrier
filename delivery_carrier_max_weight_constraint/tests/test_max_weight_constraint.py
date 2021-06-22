# Copyright 2021 ACSONE SA/NV.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.exceptions import ValidationError

from odoo.addons.stock.tests.test_packing import TestPackingCommon


class TestMaxWeightConstraint(TestPackingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.uom_kg = cls.env.ref("uom.product_uom_kgm")
        cls.product_test = cls.env["product.product"].create(
            {
                "name": "Product TEST",
                "type": "product",
                "weight": 2,
                "uom_id": cls.uom_kg.id,
                "uom_po_id": cls.uom_kg.id,
            }
        )
        carrier_product = cls.env["product.product"].create(
            {
                "name": "Test carrier product",
                "type": "service",
            }
        )
        cls.carrier = cls.env["delivery.carrier"].create(
            {
                "name": "Test carrier",
                "delivery_type": "fixed",
                "product_id": carrier_product.id,
            }
        )
        cls.package_type = cls.env["stock.package.type"].create(
            {
                "name": "Pack Type 1",
                "max_weight": 10,
            }
        )
        # make some stock available
        cls.env["stock.quant"]._update_available_quantity(
            cls.product_test, cls.stock_location, 30.0
        )

    def test_strict_weight_not_set(self):
        """
        Check that the 'choose.delivery.package' wizard is working the normal way
        The validation is ok even if the package is over the max_weight of the
        package type
        """
        # check package type hasn't weight constraint enabled
        self.assertFalse(self.package_type.is_strict_weight)

        picking_ship = self.env["stock.picking"].create(
            {
                "partner_id": self.env["res.partner"].create({"name": "A partner"}).id,
                "picking_type_id": self.warehouse.out_type_id.id,
                "location_id": self.stock_location.id,
                "location_dest_id": self.customer_location.id,
                "carrier_id": self.carrier.id,
            }
        )
        self.env["stock.move.line"].create(
            {
                "product_id": self.product_test.id,
                "product_uom_id": self.uom_kg.id,
                "picking_id": picking_ship.id,
                "qty_done": 6,
                "location_id": self.stock_location.id,
                "location_dest_id": self.customer_location.id,
            }
        )
        picking_ship.action_confirm()
        pack_action = picking_ship.action_put_in_pack()
        pack_action_ctx = pack_action["context"]

        # We instanciate the wizard with the context of the action
        # Then set the delivery package type
        pack_wiz = (
            self.env["choose.delivery.package"]
            .with_context(**pack_action_ctx)
            .create({})
        )
        # check the package is over the max_weight of package type
        self.assertGreater(pack_wiz.shipping_weight, self.package_type.max_weight)
        pack_wiz.delivery_package_type_id = self.package_type.id
        # validate the wizard
        pack_wiz.action_put_in_pack()

    def test_strict_weight_set_ok(self):
        """
        Check that the 'choose.delivery.package' wizard is working the normal way
        The validation is ok even if the package is under the max_weight of the
        package type
        """
        self.package_type.is_strict_weight = True
        # check package type hasn't weight constraint enabled
        self.assertTrue(self.package_type.is_strict_weight)

        picking_ship = self.env["stock.picking"].create(
            {
                "partner_id": self.env["res.partner"].create({"name": "A partner"}).id,
                "picking_type_id": self.warehouse.out_type_id.id,
                "location_id": self.stock_location.id,
                "location_dest_id": self.customer_location.id,
                "carrier_id": self.carrier.id,
            }
        )
        self.env["stock.move.line"].create(
            {
                "product_id": self.product_test.id,
                "product_uom_id": self.uom_kg.id,
                "picking_id": picking_ship.id,
                "qty_done": 4,
                "location_id": self.stock_location.id,
                "location_dest_id": self.customer_location.id,
            }
        )
        picking_ship.action_confirm()
        pack_action = picking_ship.action_put_in_pack()
        pack_action_ctx = pack_action["context"]

        # We instanciate the wizard with the context of the action
        # Then set the delivery package type
        pack_wiz = (
            self.env["choose.delivery.package"]
            .with_context(**pack_action_ctx)
            .create({})
        )
        # check the package is under the max_weight of package type
        self.assertGreater(self.package_type.max_weight, pack_wiz.shipping_weight)
        pack_wiz.delivery_package_type_id = self.package_type.id
        # validate the wizard
        pack_wiz.action_put_in_pack()

    def test_strict_weight_set_error(self):
        """
        Check that the 'choose.delivery.package' wizard is raising an error when
        the package is over the max_weight of the package type
        """
        self.package_type.is_strict_weight = True
        # check package type hasn't weight constraint enabled
        self.assertTrue(self.package_type.is_strict_weight)

        picking_ship = self.env["stock.picking"].create(
            {
                "partner_id": self.env["res.partner"].create({"name": "A partner"}).id,
                "picking_type_id": self.warehouse.out_type_id.id,
                "location_id": self.stock_location.id,
                "location_dest_id": self.customer_location.id,
                "carrier_id": self.carrier.id,
            }
        )
        self.env["stock.move.line"].create(
            {
                "product_id": self.product_test.id,
                "product_uom_id": self.uom_kg.id,
                "picking_id": picking_ship.id,
                "qty_done": 6,
                "location_id": self.stock_location.id,
                "location_dest_id": self.customer_location.id,
            }
        )
        picking_ship.action_confirm()
        pack_action = picking_ship.action_put_in_pack()
        pack_action_ctx = pack_action["context"]

        # We instanciate the wizard with the context of the action
        # Then set the delivery package type
        pack_wiz = (
            self.env["choose.delivery.package"]
            .with_context(**pack_action_ctx)
            .create({})
        )
        # check the package is over the max_weight of package type
        self.assertGreater(pack_wiz.shipping_weight, self.package_type.max_weight)
        error_msg = (
            "The weight of your package is higher than the maximum "
            "weight authorized for this package type. Please choose "
            "another package type."
        )
        with self.assertRaises(ValidationError, msg=error_msg):
            pack_wiz.delivery_package_type_id = self.package_type.id

    def test_strict_weight_set_max_weightb_not_set(self):
        """
        Check that the 'choose.delivery.package' wizard is working the normal way
        when the constraint is set but package type max_weight not.
        """
        self.package_type.is_strict_weight = True
        # check package type hasn't weight constraint enabled
        self.assertTrue(self.package_type.is_strict_weight)

        picking_ship = self.env["stock.picking"].create(
            {
                "partner_id": self.env["res.partner"].create({"name": "A partner"}).id,
                "picking_type_id": self.warehouse.out_type_id.id,
                "location_id": self.stock_location.id,
                "location_dest_id": self.customer_location.id,
                "carrier_id": self.carrier.id,
            }
        )
        self.env["stock.move.line"].create(
            {
                "product_id": self.product_test.id,
                "product_uom_id": self.uom_kg.id,
                "picking_id": picking_ship.id,
                "qty_done": 6,
                "location_id": self.stock_location.id,
                "location_dest_id": self.customer_location.id,
            }
        )
        picking_ship.action_confirm()
        pack_action = picking_ship.action_put_in_pack()
        pack_action_ctx = pack_action["context"]

        # We instanciate the wizard with the context of the action
        # Then set the delivery package type
        pack_wiz = (
            self.env["choose.delivery.package"]
            .with_context(**pack_action_ctx)
            .create({})
        )
        # set max_weight of package type to 0
        self.package_type.max_weight = 0
        pack_wiz.delivery_package_type_id = self.package_type.id
        # validate the wizard
        pack_wiz.action_put_in_pack()
