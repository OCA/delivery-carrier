# Copyright 2021-2021 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo_test_helper import FakeModelLoader

from .common import StockPickingDeliveryLinkCommonCase


class TestStockPickingDeliveryLink(StockPickingDeliveryLinkCommonCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product = cls.env["product.product"].create(
            {"name": "Test Product", "type": "product"}
        )
        cls.customer_location = cls.env.ref("stock.stock_location_customers")
        test_carrier_product = cls.env["product.product"].create(
            {
                "name": "Test carrier product",
                "type": "service",
            }
        )
        cls.test_carrier = cls.env["delivery.carrier"].create(
            {
                "name": "Test carrier",
                "delivery_type": "fixed",
                "product_id": test_carrier_product.id,
            }
        )
        # We need to know if purchase module is installed
        cls.purchase_installed = False
        if "purchased_product_qty" in cls.env["product.product"]._fields:
            cls.purchase_installed = True
            cls.vendor = cls.env["res.partner"].create({"name": "Test vendor"})
            cls.product.write(
                {
                    "seller_ids": [(0, 0, {"partner_id": cls.vendor.id})],
                }
            )

        cls.loader = FakeModelLoader(cls.env, cls.__module__)
        cls.loader.backup_registry()
        from .models.delivery_carrier import DeliveryCarrier

        cls.loader.update_registry((DeliveryCarrier,))

    @classmethod
    def tearDownClass(cls):
        cls.loader.restore_registry()
        super().tearDownClass()

    def test_ship_data_from_pick(self):
        move1 = self._create_move(
            self.product,
            self.stock_loc,
            self.shelf1_loc,
            picking_type_id=self.wh.pick_type_id.id,
        )
        move2 = self._create_move(
            self.product,
            self.stock_loc,
            self.shelf1_loc,
            picking_type_id=self.wh.pack_type_id.id,
        )
        move3 = self._create_move(
            self.product,
            self.shelf1_loc,
            self.shelf2_loc,
            picking_type_id=self.wh.out_type_id.id,
        )
        (move1 | move2 | move3)._assign_picking()
        carrier = self.env.ref("delivery.free_delivery_carrier")
        move3.picking_id.carrier_id = carrier
        move1.move_dest_ids = move2
        move2.move_dest_ids = move3
        ship = move1.picking_id.ship_picking_id
        self.assertEqual(ship, move3.picking_id)
        self.assertEqual(ship.carrier_id, carrier)

    def test_ship_data_from_pack(self):
        move1 = self._create_move(
            self.product,
            self.stock_loc,
            self.shelf1_loc,
            picking_type_id=self.wh.pack_type_id.id,
        )
        move2 = self._create_move(
            self.product,
            self.shelf1_loc,
            self.shelf2_loc,
            picking_type_id=self.wh.out_type_id.id,
        )
        (move1 | move2)._assign_picking()
        carrier = self.env.ref("delivery.free_delivery_carrier")
        move2.picking_id.carrier_id = carrier
        move1.move_dest_ids = move2
        ship = move1.picking_id.ship_picking_id
        self.assertEqual(ship, move2.picking_id)
        self.assertEqual(ship.carrier_id, carrier)

    def test_ship_data_no_ship_found(self):
        move1 = self._create_move(
            self.product,
            self.stock_loc,
            self.shelf1_loc,
            picking_type_id=self.wh.pick_type_id.id,
        )
        move2 = self._create_move(
            self.product,
            self.shelf1_loc,
            self.shelf2_loc,
            picking_type_id=self.wh.pack_type_id.id,
        )
        (move1 | move2)._assign_picking()
        move1.move_dest_ids = move2
        self.assertFalse(move1.picking_id.ship_picking_id)
        self.assertFalse(move1.picking_id.ship_carrier_id)

    def test_put_in_pack_from_pick_with_wizard(self):
        """
        Normally the "choose package type" wizard is triggered only if a carrier is
        set on the picking (usually on ship picking). This module permits to force
        the wizard if there is no carrier set but if there is a shipping carrier and
        set_delivery_package_type_on_put_in_pack set on the package type.

        Try with forcing from pick picking type => wizard ok
        """
        self.wh.delivery_steps = "pick_ship"
        self.env["stock.quant"]._update_available_quantity(
            self.product, self.shelf1_loc, 20.0
        )
        ship_move = self.env["stock.move"].create(
            {
                "name": "The ship move",
                "product_id": self.product.id,
                "product_uom_qty": 5.0,
                "product_uom": self.product.uom_id.id,
                "location_id": self.shelf2_loc.id,
                "location_dest_id": self.customer_location.id,
                "warehouse_id": self.wh.id,
                "picking_type_id": self.wh.out_type_id.id,
                "procure_method": "make_to_order",
                "state": "draft",
            }
        )
        ship_move._assign_picking()
        ship_move._action_confirm()
        # Confirm purchase order
        if self.purchase_installed:
            purchase = self.env["purchase.order"].search(
                [("partner_id", "=", self.vendor.id)]
            )
            purchase.button_confirm()
        pick_move = ship_move.move_orig_ids[0]
        pick_picking = pick_move.picking_id
        ship_picking = ship_move.picking_id
        # set a carrier on shipment picking
        ship_picking.carrier_id = self.test_carrier
        # force wizard on pick operation picking_type_id
        pick_picking.picking_type_id.set_delivery_package_type_on_put_in_pack = True
        pick_picking.action_assign()
        pick_picking.move_line_ids.filtered(
            lambda ml: ml.product_id == self.product
        ).qty_done = 5.0
        pip_action = pick_picking.action_put_in_pack()
        # check the action is a dict
        self.assertIsInstance(pip_action, dict)
        pip_action_model = pip_action["res_model"]
        pip_action_context = pip_action["context"]
        # We make sure the correct action was returned
        self.assertEqual(pip_action_model, "choose.delivery.package")
        self.assertEqual("none", pip_action_context.get("current_package_carrier_type"))

    def test_put_in_pack_from_pick_with_wizard_carrier(self):
        """
        Normally the "choose package type" wizard is triggered only if a carrier is
        set on the picking (usually on ship picking). This module permits to force
        the wizard if there is no carrier set but if there is a shipping carrier and
        set_delivery_package_type_on_put_in_pack set on the package type.

        Try with forcing from pick picking type => wizard ok
        """
        self.test_carrier.delivery_type = "test"
        self.wh.delivery_steps = "pick_ship"
        self.env["stock.quant"]._update_available_quantity(
            self.product, self.shelf1_loc, 20.0
        )
        ship_move = self.env["stock.move"].create(
            {
                "name": "The ship move",
                "product_id": self.product.id,
                "product_uom_qty": 5.0,
                "product_uom": self.product.uom_id.id,
                "location_id": self.shelf2_loc.id,
                "location_dest_id": self.customer_location.id,
                "warehouse_id": self.wh.id,
                "picking_type_id": self.wh.out_type_id.id,
                "procure_method": "make_to_order",
                "state": "draft",
            }
        )
        ship_move._assign_picking()
        ship_move._action_confirm()
        # Confirm purchase order
        if self.purchase_installed:
            purchase = self.env["purchase.order"].search(
                [("partner_id", "=", self.vendor.id)]
            )
            purchase.button_confirm()
        pick_move = ship_move.move_orig_ids[0]
        pick_picking = pick_move.picking_id
        ship_picking = ship_move.picking_id
        # set a carrier on shipment picking
        ship_picking.carrier_id = self.test_carrier
        # force wizard on pick operation picking_type_id
        pick_picking.picking_type_id.set_delivery_package_type_on_put_in_pack = True
        pick_picking.action_assign()
        pick_picking.move_line_ids.filtered(
            lambda ml: ml.product_id == self.product
        ).qty_done = 5.0
        pip_action = pick_picking.action_put_in_pack()
        # check the action is a dict
        self.assertIsInstance(pip_action, dict)
        pip_action_model = pip_action["res_model"]
        pip_action_context = pip_action["context"]
        # We make sure the correct action was returned
        self.assertEqual(pip_action_model, "choose.delivery.package")
        self.assertEqual("test", pip_action_context.get("current_package_carrier_type"))

    def test_put_in_pack_from_pick_without_wizard(self):
        """
        Normally the "choose package type" wizard is triggered only if a carrier is
        set on the picking (usually on ship picking). This module permits to force
        the wizard if there is no carrier set but if there is a carrier on shipment
        picking and set_delivery_package_type_on_put_in_pack set on the picking type.

        Try without forcing from pick picking type => no wizard
        """
        self.wh.delivery_steps = "pick_ship"
        self.env["stock.quant"]._update_available_quantity(
            self.product, self.shelf1_loc, 20.0
        )
        ship_move = self.env["stock.move"].create(
            {
                "name": "The ship move",
                "product_id": self.product.id,
                "product_uom_qty": 5.0,
                "product_uom": self.product.uom_id.id,
                "location_id": self.shelf2_loc.id,
                "location_dest_id": self.customer_location.id,
                "warehouse_id": self.wh.id,
                "picking_type_id": self.wh.out_type_id.id,
                "procure_method": "make_to_order",
                "state": "draft",
            }
        )
        ship_move._assign_picking()
        ship_move._action_confirm()
        # Confirm purchase order
        if self.purchase_installed:
            purchase = self.env["purchase.order"].search(
                [("partner_id", "=", self.vendor.id)]
            )
            purchase.button_confirm()
        pick_move = ship_move.move_orig_ids[0]
        pick_picking = pick_move.picking_id
        ship_picking = ship_move.picking_id
        # set a carrier on shipment picking but do not force wizard on picking type
        ship_picking.carrier_id = self.test_carrier
        pick_picking.action_assign()
        pick_picking.move_line_ids.filtered(
            lambda ml: ml.product_id == self.product
        ).qty_done = 5.0
        pip_action = pick_picking.action_put_in_pack()
        # the action is not a dict so not a wizard
        self.assertNotIsInstance(pip_action, dict)

    def test_put_in_pack_from_ship_with_wizard(self):
        """
        Let the warehouse configuration to one step delivery
        Create a delivery picking
        Set a carrier on it
        Launch the put in pack operation
        The current_package_carrier_type in context should be 'none'
        """
        self.wh.delivery_steps = "ship_only"
        self.env["stock.quant"]._update_available_quantity(
            self.product, self.shelf1_loc, 20.0
        )
        ship_move = self.env["stock.move"].create(
            {
                "name": "The ship move",
                "product_id": self.product.id,
                "product_uom_qty": 5.0,
                "product_uom": self.product.uom_id.id,
                "location_id": self.shelf1_loc.id,
                "location_dest_id": self.customer_location.id,
                "warehouse_id": self.wh.id,
                "picking_type_id": self.wh.out_type_id.id,
                "procure_method": "make_to_stock",
                "state": "draft",
            }
        )

        ship_move._action_confirm()
        ship_move._assign_picking()
        ship_move.picking_id.carrier_id = self.test_carrier

        res = ship_move.picking_id.action_put_in_pack()
        carrier_type = res["context"].get("current_package_carrier_type")
        self.assertEqual("none", carrier_type)
