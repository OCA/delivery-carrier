# Copyright 2026 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests import tagged

from .common import StockPickingDeliveryLinkCommonCase


# post_install: can run on an installed database without updating the module
@tagged("post_install", "-at_install")
class TestShipChainQueries(StockPickingDeliveryLinkCommonCase):
    """The number of queries depends on the depth of the chains only."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product = cls.env["product.product"].create(
            {"name": "Test Product", "type": "consu", "is_storable": True}
        )

    def _create_chain(self, picking_types):
        """Create one move per picking type, each chained to the next one.

        Each chain has its own procurement group and goes through the test
        locations, so that its moves get their own pickings.
        """
        group = self.env["procurement.group"].create({"name": "chain"})
        moves = self.env["stock.move"]
        for picking_type in picking_types:
            moves |= self._create_move(
                self.product,
                self.shelf1_loc,
                self.shelf2_loc,
                picking_type_id=picking_type.id,
                group_id=group.id,
            )
        moves._assign_picking()
        for move, next_move in zip(moves, moves[1:]):
            move.move_dest_ids = next_move
        return moves

    def _create_pickings(self, count):
        """Create ``count`` pick > pack > ship chains, return the picks."""
        wh = self.wh
        picking_types = [wh.pick_type_id, wh.pack_type_id, wh.out_type_id]
        pickings = self.env["stock.picking"]
        for __ in range(count):
            pickings |= self._create_chain(picking_types)[0].picking_id
        return pickings

    def _assert_ship_queries(self, pickings, count):
        self.env.flush_all()
        self.env.invalidate_all()
        # 1 query for the moves of the pickings, then 3 per level of the
        # chain: destination moves, their origin moves, outgoing pickings
        with self.assertQueryCount(count):
            ship_by_picking = pickings._get_ship_by_picking_id()
        self.assertEqual(set(ship_by_picking), set(pickings.ids))

    def test_queries_do_not_depend_on_pickings_count(self):
        self._assert_ship_queries(self._create_pickings(1), 7)
        self._assert_ship_queries(self._create_pickings(10), 7)
