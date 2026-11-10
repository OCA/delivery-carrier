# Copyright 2021-2021 Camptocamp SA
# @author Simone Orsi <simone.orsi@camptocamp.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from datetime import timedelta

from odoo_test_helper import FakeModelLoader

from odoo import fields
from odoo.tests import new_test_user

from .common import StockPickingDeliveryLinkCommonCase


class TestStockPickingDeliveryLink(StockPickingDeliveryLinkCommonCase):
    """Resolution of the delivery (``ship_picking_id``) through the move chain.

    The deliveries are found by following, from the moves of the picking,
    all the destination moves not done nor cancelled, until moves in
    outgoing pickings are reached. When several deliveries are reached, the
    most urgent one wins (``stock.picking`` order: priority, then scheduled
    date, then id).

    Covered use cases:

    * linear chains: pick > pack > ship, pack > ship, and a deeper chain
      with several internal steps before the delivery;
    * no delivery in the chain: no outgoing picking is reached;
    * no destination move at all;
    * done and cancelled destination moves are skipped;
    * ``done=True`` variant: only done or cancelled destination moves are
      followed;
    * fork: a move with several destination moves reaching deliveries, the
      most urgent delivery wins, then the earliest scheduled one;
    * several moves in the source picking: the most urgent delivery wins;
    * dead end branch: the deliveries of the other branches are found;
    * merge: several moves of the picking leading to the same destination
      move;
    * destination move without picking in the middle of the chain;
    * source picking that is itself outgoing: the search starts from its
      destination moves, the picking itself is never returned;
    * several pickings computed at once, with different results;
    * multi-company: destination moves of companies not allowed for the
      user are ignored, as with the ORM record rules;
    * pending (not flushed) changes are taken into account;
    * chain looping on itself: the resolution stops without result;
    * the number of queries depends on the depth of the chains, not on the
      number of pickings.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product = cls.env["product.product"].create(
            {"name": "Test Product", "type": "consu", "is_storable": True}
        )
        cls.customer_location = cls.env.ref("stock.stock_location_customers")
        cls.pick_type = cls.wh.pick_type_id
        cls.pack_type = cls.wh.pack_type_id
        cls.out_type = cls.wh.out_type_id
        cls.carrier = cls.env.ref("delivery.free_delivery_carrier")
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

    def setUp(self):
        super().setUp()
        self.loader = FakeModelLoader(self.env, self.__module__)
        self.loader.backup_registry()
        from .models.delivery_carrier import DeliveryCarrier

        self.loader.update_registry((DeliveryCarrier,))

    def tearDown(self):
        self.loader.restore_registry()
        return super().tearDown()

    def _create_picking(self, picking_type, **values):
        """Create a picking of ``picking_type`` between test locations."""
        values.update(
            picking_type_id=picking_type.id,
            location_id=self.stock_loc.id,
            location_dest_id=self.shelf1_loc.id,
        )
        return self.env["stock.picking"].create(values)

    def _create_chain_move(self, picking=None, **values):
        """Create a move, in ``picking`` when given."""
        if picking:
            values.update(
                picking_id=picking.id,
                picking_type_id=picking.picking_type_id.id,
            )
        return self._create_move(
            self.product, self.stock_loc, self.shelf1_loc, **values
        )

    def _reload(self):
        """Drop the cache to read the chain as stored."""
        self.env.invalidate_all()

    def _assert_ship(self, picking, expected, done=False):
        """Check the delivery found from ``picking``, and its computed fields."""
        self.assertEqual(picking._get_ship_from_chain(done=done), expected)
        if not done:
            self.assertEqual(picking.ship_picking_id, expected)
            self.assertEqual(picking.ship_carrier_id, expected.carrier_id)

    def test_ship_data_from_pick(self):
        """Pick > pack > ship: the pick is linked to the ship and its carrier."""
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
        """Pack > ship: the pack is linked to the ship and its carrier."""
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
        """No outgoing picking in the chain: no delivery nor carrier."""
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

    def test_ship_data_deep_chain(self):
        """Delivery found after several internal steps."""
        pick = self._create_picking(self.pick_type)
        move = self._create_chain_move(pick)
        for __ in range(4):
            next_move = self._create_chain_move(self._create_picking(self.pack_type))
            move.move_dest_ids = next_move
            move = next_move
        ship = self._create_picking(self.out_type, carrier_id=self.carrier.id)
        ship_move = self._create_chain_move(ship)
        move.move_dest_ids = ship_move
        self._assert_ship(pick, ship)

    def test_ship_data_no_dest_move(self):
        """Picking without destination move: no delivery."""
        pick = self._create_picking(self.pick_type)
        self._create_chain_move(pick)
        self._assert_ship(pick, self.env["stock.picking"])

    def test_ship_data_skip_done_and_cancelled_dest(self):
        """Done and cancelled destination moves are skipped."""
        pick = self._create_picking(self.pick_type)
        move = self._create_chain_move(pick)
        ship_done = self._create_picking(self.out_type)
        move_done = self._create_chain_move(ship_done, sequence=1)
        ship_cancel = self._create_picking(self.out_type)
        move_cancel = self._create_chain_move(ship_cancel, sequence=2)
        ship_open = self._create_picking(self.out_type, carrier_id=self.carrier.id)
        move_open = self._create_chain_move(ship_open, sequence=3)
        move.move_dest_ids = move_done | move_cancel | move_open
        move_done.state = "done"
        move_cancel.state = "cancel"
        self._assert_ship(pick, ship_open)

    def test_ship_data_done_variant(self):
        """With ``done=True`` only done or cancelled moves are followed."""
        pick = self._create_picking(self.pick_type)
        move = self._create_chain_move(pick)
        ship_open = self._create_picking(self.out_type)
        move_open = self._create_chain_move(ship_open, sequence=1)
        ship_done = self._create_picking(self.out_type)
        move_done = self._create_chain_move(ship_done, sequence=2)
        move.move_dest_ids = move_open | move_done
        move_done.state = "done"
        self._assert_ship(pick, ship_done, done=True)
        self._assert_ship(pick, ship_open)

    def test_ship_data_done_variant_cancelled(self):
        """With ``done=True`` cancelled moves are followed too."""
        pick = self._create_picking(self.pick_type)
        move = self._create_chain_move(pick)
        ship_open = self._create_picking(self.out_type)
        move_open = self._create_chain_move(ship_open, sequence=1)
        ship_cancel = self._create_picking(self.out_type)
        move_cancel = self._create_chain_move(ship_cancel, sequence=2)
        move.move_dest_ids = move_open | move_cancel
        move_cancel.state = "cancel"
        self._assert_ship(pick, ship_cancel, done=True)
        self._assert_ship(pick, ship_open)

    def test_ship_data_fork_by_priority(self):
        """Fork: the most urgent delivery wins."""
        pick = self._create_picking(self.pick_type)
        move = self._create_chain_move(pick)
        # first destination move by sequence, but not urgent
        ship_normal = self._create_picking(self.out_type)
        move_normal = self._create_chain_move(ship_normal, sequence=10)
        ship_urgent = self._create_picking(self.out_type, priority="1")
        move_urgent = self._create_chain_move(ship_urgent, sequence=20)
        move.move_dest_ids = move_normal | move_urgent
        self._assert_ship(pick, ship_urgent)

    def test_ship_data_fork_same_priority_by_date(self):
        """Fork with equal priorities: the earliest scheduled delivery wins."""
        pick = self._create_picking(self.pick_type)
        move = self._create_chain_move(pick)
        ship_early = self._create_picking(self.out_type)
        move_early = self._create_chain_move(ship_early)
        ship_late = self._create_picking(self.out_type)
        move_late = self._create_chain_move(ship_late)
        now = fields.Datetime.now()
        ship_early.scheduled_date = now
        # created last (highest id) but scheduled later
        ship_late.scheduled_date = now + timedelta(days=1)
        move.move_dest_ids = move_late | move_early
        self._assert_ship(pick, ship_early)

    def test_ship_data_several_moves_by_priority(self):
        """Several source moves: the most urgent delivery wins."""
        pick = self._create_picking(self.pick_type)
        # first source move by sequence, leading to the normal delivery
        move_first = self._create_chain_move(pick, sequence=10)
        move_second = self._create_chain_move(pick, sequence=20)
        ship_normal = self._create_picking(self.out_type)
        ship_urgent = self._create_picking(self.out_type, priority="1")
        move_first.move_dest_ids = self._create_chain_move(ship_normal)
        move_second.move_dest_ids = self._create_chain_move(ship_urgent)
        self._assert_ship(pick, ship_urgent)

    def test_ship_data_dead_end_branch(self):
        """First branch is a dead end: the other branch's delivery is found."""
        pick = self._create_picking(self.pick_type)
        move = self._create_chain_move(pick)
        # first branch: dead end in an internal picking
        dead_end = self._create_chain_move(
            self._create_picking(self.pack_type), sequence=1
        )
        # second branch: leads to a delivery
        ship = self._create_picking(self.out_type)
        move.move_dest_ids = dead_end | self._create_chain_move(ship, sequence=2)
        self._assert_ship(pick, ship)

    def test_ship_data_merge(self):
        """Several moves leading to the same delivery move: delivery found."""
        pick = self._create_picking(self.pick_type)
        move1 = self._create_chain_move(pick)
        move2 = self._create_chain_move(pick)
        ship = self._create_picking(self.out_type, carrier_id=self.carrier.id)
        ship_move = self._create_chain_move(ship)
        (move1 | move2).move_dest_ids = ship_move
        self._assert_ship(pick, ship)

    def test_ship_data_dest_move_without_picking(self):
        """A move without picking in the chain is followed."""
        pick = self._create_picking(self.pick_type)
        move = self._create_chain_move(pick)
        loose_move = self._create_chain_move()
        self.assertFalse(loose_move.picking_id)
        ship = self._create_picking(self.out_type, carrier_id=self.carrier.id)
        move.move_dest_ids = loose_move
        loose_move.move_dest_ids = self._create_chain_move(ship)
        self._assert_ship(pick, ship)

    def test_ship_data_from_outgoing_picking(self):
        """Outgoing picking: never itself, only a next delivery."""
        out1 = self._create_picking(self.out_type)
        move = self._create_chain_move(out1)
        # no destination: the outgoing picking itself is not returned
        self._assert_ship(out1, self.env["stock.picking"])
        out2 = self._create_picking(self.out_type)
        move.move_dest_ids = self._create_chain_move(out2)
        self.env.invalidate_all()
        self._assert_ship(out1, out2)

    def test_ship_data_several_pickings(self):
        """Several pickings at once: each one gets its own delivery."""
        ship = self._create_picking(self.out_type, carrier_id=self.carrier.id)
        pick_with_ship = self._create_picking(self.pick_type)
        self._create_chain_move(pick_with_ship).move_dest_ids = self._create_chain_move(
            ship
        )
        pick_without_ship = self._create_picking(self.pick_type)
        self._create_chain_move(
            pick_without_ship
        ).move_dest_ids = self._create_chain_move(self._create_picking(self.pack_type))
        pick_no_dest = self._create_picking(self.pick_type)
        self._create_chain_move(pick_no_dest)
        pickings = pick_with_ship | pick_without_ship | pick_no_dest
        pickings.invalidate_recordset(["ship_picking_id", "ship_carrier_id"])
        # read on the whole recordset: computed in one call
        self.assertEqual(pickings.mapped("ship_picking_id"), ship)
        self.assertEqual(pick_with_ship.ship_picking_id, ship)
        self.assertEqual(pick_with_ship.ship_carrier_id, self.carrier)
        self.assertFalse(pick_without_ship.ship_picking_id)
        self.assertFalse(pick_no_dest.ship_picking_id)

    def test_ship_data_multi_company(self):
        """Moves of companies not allowed for the user are ignored."""
        company_a = self.env.company
        company_b = self.env["res.company"].create({"name": "Company B"})
        wh_b = self.env["stock.warehouse"].search(
            [("company_id", "=", company_b.id)], limit=1
        )
        pick = self._create_picking(self.pick_type)
        move = self._create_chain_move(pick)
        ship_b = self.env["stock.picking"].create(
            {
                "picking_type_id": wh_b.out_type_id.id,
                "location_id": wh_b.lot_stock_id.id,
                "location_dest_id": self.env.ref("stock.stock_location_customers").id,
                "company_id": company_b.id,
                # most urgent: wins when its company is visible
                "priority": "1",
            }
        )
        move_b = self._create_move(
            self.product,
            wh_b.lot_stock_id,
            self.env.ref("stock.stock_location_customers"),
            picking_id=ship_b.id,
            picking_type_id=ship_b.picking_type_id.id,
            company_id=company_b.id,
            sequence=1,
        )
        ship_a = self._create_picking(self.out_type)
        move_a = self._create_chain_move(ship_a, sequence=2)
        move.move_dest_ids = move_b | move_a
        user = new_test_user(
            self.env,
            login="stock_user_company_a",
            groups="stock.group_stock_user",
            company_id=company_a.id,
            company_ids=[company_a.id],
        )
        self.env.invalidate_all()
        # company B is not allowed for the user: its move is ignored
        self.assertEqual(pick.with_user(user)._get_ship_from_chain(), ship_a)
        self.env.invalidate_all()
        # as superuser, all companies are visible
        self.assertEqual(pick.sudo()._get_ship_from_chain(), ship_b)

    def test_ship_data_pending_changes(self):
        """Chain changes not flushed yet are taken into account."""
        pick = self._create_picking(self.pick_type)
        move = self._create_chain_move(pick)
        ship1 = self._create_picking(self.out_type)
        move1 = self._create_chain_move(ship1)
        move.move_dest_ids = move1
        self._assert_ship(pick, ship1)
        # change the chain without flushing
        ship2 = self._create_picking(self.out_type)
        move2 = self._create_chain_move(ship2, sequence=1)
        move.move_dest_ids = move2
        move1.state = "cancel"
        pick.invalidate_recordset(["ship_picking_id", "ship_carrier_id"])
        self._assert_ship(pick, ship2)

    def test_ship_data_cycle(self):
        """Chain looping on itself: resolution stops without delivery."""
        pick = self._create_picking(self.pick_type)
        move = self._create_chain_move(pick)
        move2 = self._create_chain_move(self._create_picking(self.pack_type))
        move3 = self._create_chain_move(self._create_picking(self.pack_type))
        move.move_dest_ids = move2
        move2.move_dest_ids = move3
        move3.move_dest_ids = move2
        self._assert_ship(pick, self.env["stock.picking"])

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
        pick_line = pick_picking.move_line_ids.filtered(
            lambda ml: ml.product_id == self.product
        )
        self.assertEqual(pick_line.quantity, 5)
        pick_line.picked = True
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
        pick_line = pick_picking.move_line_ids.filtered(
            lambda ml: ml.product_id == self.product
        )
        self.assertEqual(pick_line.quantity, 5)
        pick_line.picked = True
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
        pick_line = pick_picking.move_line_ids.filtered(
            lambda ml: ml.product_id == self.product
        )
        self.assertEqual(pick_line.quantity, 5)
        pick_line.picked = True
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
        group = self.env["procurement.group"].create({"name": "Test group"})
        ship_move = self.env["stock.move"].create(
            {
                "name": "The ship move",
                "group_id": group.id,
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
        ship_move.picking_id.carrier_id = self.test_carrier

        res = ship_move.picking_id.action_put_in_pack()
        carrier_type = res["context"].get("current_package_carrier_type")
        self.assertEqual("none", carrier_type)

    def _create_chains(self, count, depth):
        """Create ``count`` pickings chained to a delivery in ``depth`` steps."""
        pickings = self.env["stock.picking"]
        for __ in range(count):
            pick = self._create_picking(self.pick_type)
            move = self._create_chain_move(pick)
            for __ in range(depth - 1):
                next_move = self._create_chain_move(
                    self._create_picking(self.pack_type)
                )
                move.move_dest_ids = next_move
                move = next_move
            ship = self._create_picking(self.out_type)
            move.move_dest_ids = self._create_chain_move(ship)
            pickings |= pick
        self.env.flush_all()
        return pickings

    def test_ship_data_query_count(self):
        """Queries depend on the chain depth, not on the number of pickings.

        1 query for the moves of the pickings, then 3 per level of the chain:
        destination moves, their origin moves, outgoing pickings.
        """
        one = self._create_chains(1, 1)
        many = self._create_chains(10, 1)
        many_deep = self._create_chains(10, 5)
        self._reload()
        with self.assertQueryCount(4):
            ships = one._get_ship_by_picking_id()
        self.assertEqual(len(ships), 1)
        with self.assertQueryCount(4):
            ships = many._get_ship_by_picking_id()
        self.assertEqual(len(ships), 10)
        with self.assertQueryCount(16):
            ships = many_deep._get_ship_by_picking_id()
        self.assertEqual(len(ships), 10)
