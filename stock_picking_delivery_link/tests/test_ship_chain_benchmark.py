# Copyright 2026 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
import time

from ..models.stock_picking import get_first_move_dest
from .common import StockPickingDeliveryLinkCommonCase

_logger = logging.getLogger(__name__)


def legacy_ship_from_chain(picking, done=False):
    """Previous implementation: walk the chain with the ORM."""
    move_dest = get_first_move_dest(picking.move_ids, done=done)
    while move_dest:
        ship = move_dest.picking_id
        if ship.picking_type_id.code == "outgoing":
            return ship
        move_dest = get_first_move_dest(move_dest, done=done)
    return picking.browse()


class TestShipChainBenchmark(StockPickingDeliveryLinkCommonCase):
    """Compare the SQL resolution of the ship chain with the ORM walk.

    Both implementations must return the same deliveries, the SQL one with
    a single query. Timings (best of several warm runs) are logged, not
    asserted: they depend on the machine and on the database size.

    Measured on a production database copy (10M stock moves, PostgreSQL
    14, warm cache, best of several runs), all results identical:

    =================================  ===============  ===========  =====
    Pickings                           ORM walk         SQL          Gain
    =================================  ===============  ===========  =====
    11 (zone picking request)          14.6 ms, 6 q     4.3 ms, 1 q  x3.4
    3 (chains of depth 3)              29.2 ms, 13 q    4.2 ms, 1 q  x6.9
    2535 (all open pickings)           809 ms, 40 q     446 ms, 1 q  x1.8
    =================================  ===============  ===========  =====
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product = cls.env["product.product"].create(
            {"name": "Test Product", "type": "consu", "is_storable": True}
        )

    def _create_picking(self, picking_type):
        return self.env["stock.picking"].create(
            {
                "picking_type_id": picking_type.id,
                "location_id": self.stock_loc.id,
                "location_dest_id": self.shelf1_loc.id,
            }
        )

    def _create_chain(self, depth, with_ship=True):
        picking = self._create_picking(self.wh.pick_type_id)
        move = self._create_move(
            self.product,
            self.stock_loc,
            self.shelf1_loc,
            picking_id=picking.id,
            picking_type_id=picking.picking_type_id.id,
        )
        for step in range(depth):
            last = step == depth - 1
            picking_type = (
                self.wh.out_type_id if last and with_ship else self.wh.pack_type_id
            )
            next_picking = self._create_picking(picking_type)
            next_move = self._create_move(
                self.product,
                self.stock_loc,
                self.shelf1_loc,
                picking_id=next_picking.id,
                picking_type_id=picking_type.id,
            )
            move.move_dest_ids = next_move
            move = next_move
        return picking

    def _measure(self, func, rounds=5):
        """Return the result, best time and query count of ``func``.

        The first round warms up the connection (catalog, query planning)
        and is not measured, the cache is dropped before each round.
        """
        best = None
        for round_ in range(rounds + 1):
            self.env.invalidate_all()
            count = self.cr.sql_log_count
            start = time.perf_counter()
            result = func()
            elapsed = time.perf_counter() - start
            queries = self.cr.sql_log_count - count
            if round_:
                best = elapsed if best is None else min(best, elapsed)
        return result, best, queries

    def test_benchmark(self):
        pickings = self.env["stock.picking"]
        for index in range(30):
            pickings |= self._create_chain(depth=index % 4 + 1, with_ship=index % 5)
        # test databases have no statistics: without them the planner
        # misestimates the recursive query (sequential scans, JIT)
        self.env.flush_all()
        self.cr.execute("ANALYZE stock_move, stock_move_move_rel, stock_picking")
        old, old_time, old_queries = self._measure(
            lambda: {p.id: legacy_ship_from_chain(p) for p in pickings}
        )
        new, new_time, new_queries = self._measure(pickings._get_ships_from_chain)
        for picking in pickings:
            self.assertEqual(new.get(picking.id, picking.browse()), old[picking.id])
        self.assertEqual(new_queries, 1)
        self.assertLess(new_queries, old_queries)
        _logger.info(
            "Ship chain of %s pickings: ORM walk %.1f ms (%s queries), "
            "SQL %.1f ms (%s query), gain x%.1f",
            len(pickings),
            old_time * 1000,
            old_queries,
            new_time * 1000,
            new_queries,
            old_time / new_time,
        )
