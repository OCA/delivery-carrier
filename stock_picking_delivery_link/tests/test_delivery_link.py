# Copyright 2021-2021 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests import new_test_user

from .common import StockPickingDeliveryLinkCommonCase


class TestStockPickingDeliveryLink(StockPickingDeliveryLinkCommonCase):
    """Resolution of the delivery (``ship_picking_id``) through the move chain.

    The delivery is found by following, from the moves of the picking, the
    first destination move (by ``sequence, id``) that is not done or
    cancelled, until a move in an outgoing picking is reached.

    Covered use cases:

    * linear chains: pick > pack > ship, pack > ship, and a deeper chain
      with several internal steps before the delivery;
    * no delivery in the chain: no outgoing picking is reached;
    * no destination move at all;
    * done and cancelled destination moves are skipped;
    * ``done=True`` variant: only done or cancelled destination moves are
      followed;
    * fork: a move with several destination moves follows the first one by
      ``sequence``, then by ``id`` when sequences are equal;
    * several moves in the source picking: the first move by ``sequence``
      decides which branch is followed;
    * no backtracking: when the first branch never reaches a delivery, the
      other branches are not explored;
    * merge: several moves of the picking leading to the same destination
      move;
    * destination move without picking in the middle of the chain;
    * source picking that is itself outgoing: the search starts from its
      destination moves, the picking itself is never returned;
    * several pickings computed at once, with different results;
    * multi-company: destination moves of companies not allowed for the
      user are ignored, as with the ORM record rules;
    * pending (not flushed) changes are taken into account.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product = cls.env["product.product"].create(
            {"name": "Test Product", "type": "consu", "is_storable": True}
        )
        cls.pick_type = cls.wh.pick_type_id
        cls.pack_type = cls.wh.pack_type_id
        cls.out_type = cls.wh.out_type_id
        cls.carrier = cls.env.ref("delivery.free_delivery_carrier")

    def _create_picking(self, picking_type, **values):
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
        """Flush and drop the cache to read the chain as stored.

        Values assigned to x2many fields keep the assignment order in cache,
        the ``sequence, id`` order only applies once read from the database.
        """
        self.env.invalidate_all()

    def _assert_ship(self, picking, expected, done=False):
        self.assertEqual(picking._get_ship_from_chain(done=done), expected)
        if not done:
            self.assertEqual(picking.ship_picking_id, expected)
            self.assertEqual(picking.ship_carrier_id, expected.carrier_id)

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

    def test_ship_data_deep_chain(self):
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
        pick = self._create_picking(self.pick_type)
        self._create_chain_move(pick)
        self._assert_ship(pick, self.env["stock.picking"])

    def test_ship_data_skip_done_and_cancelled_dest(self):
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

    def test_ship_data_fork_by_sequence(self):
        pick = self._create_picking(self.pick_type)
        move = self._create_chain_move(pick)
        # created first (lower id) but with a higher sequence
        ship_late = self._create_picking(self.out_type)
        move_late = self._create_chain_move(ship_late, sequence=20)
        ship_first = self._create_picking(self.out_type)
        move_first = self._create_chain_move(ship_first, sequence=10)
        move.move_dest_ids = move_late | move_first
        self._reload()
        self._assert_ship(pick, ship_first)

    def test_ship_data_fork_same_sequence_by_id(self):
        pick = self._create_picking(self.pick_type)
        move = self._create_chain_move(pick)
        ship_first = self._create_picking(self.out_type)
        move_first = self._create_chain_move(ship_first, sequence=10)
        ship_second = self._create_picking(self.out_type)
        move_second = self._create_chain_move(ship_second, sequence=10)
        move.move_dest_ids = move_second | move_first
        self._reload()
        self._assert_ship(pick, ship_first)

    def test_ship_data_several_moves_first_by_sequence(self):
        pick = self._create_picking(self.pick_type)
        # created first (lower id) but with a higher sequence
        move_late = self._create_chain_move(pick, sequence=20)
        move_first = self._create_chain_move(pick, sequence=10)
        ship_late = self._create_picking(self.out_type)
        ship_first = self._create_picking(self.out_type)
        # dest move of the first source move has the highest sequence
        move_late.move_dest_ids = self._create_chain_move(ship_late, sequence=1)
        move_first.move_dest_ids = self._create_chain_move(ship_first, sequence=50)
        self._reload()
        self._assert_ship(pick, ship_first)

    def test_ship_data_no_backtracking(self):
        pick = self._create_picking(self.pick_type)
        move = self._create_chain_move(pick)
        # first branch: dead end in an internal picking
        dead_end = self._create_chain_move(
            self._create_picking(self.pack_type), sequence=1
        )
        # second branch: leads to a delivery
        ship = self._create_picking(self.out_type)
        move.move_dest_ids = dead_end | self._create_chain_move(ship, sequence=2)
        self._assert_ship(pick, self.env["stock.picking"])

    def test_ship_data_merge(self):
        pick = self._create_picking(self.pick_type)
        move1 = self._create_chain_move(pick)
        move2 = self._create_chain_move(pick)
        ship = self._create_picking(self.out_type, carrier_id=self.carrier.id)
        ship_move = self._create_chain_move(ship)
        (move1 | move2).move_dest_ids = ship_move
        self._assert_ship(pick, ship)

    def test_ship_data_dest_move_without_picking(self):
        pick = self._create_picking(self.pick_type)
        move = self._create_chain_move(pick)
        loose_move = self._create_chain_move()
        self.assertFalse(loose_move.picking_id)
        ship = self._create_picking(self.out_type, carrier_id=self.carrier.id)
        move.move_dest_ids = loose_move
        loose_move.move_dest_ids = self._create_chain_move(ship)
        self._assert_ship(pick, ship)

    def test_ship_data_from_outgoing_picking(self):
        out1 = self._create_picking(self.out_type)
        move = self._create_chain_move(out1)
        # no destination: the outgoing picking itself is not returned
        self._assert_ship(out1, self.env["stock.picking"])
        out2 = self._create_picking(self.out_type)
        move.move_dest_ids = self._create_chain_move(out2)
        self.env.invalidate_all()
        self._assert_ship(out1, out2)

    def test_ship_data_several_pickings(self):
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
