# Copyright 2026 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from collections import defaultdict
from operator import attrgetter

from odoo import api, models


class StockMove(models.Model):
    _inherit = "stock.move"

    def _get_ship_ids_by_chain(self, chain_key=None, done=False):
        """Return the shipments reached by each chain of moves.

        See ``_walk_dest_chains``: chains end at moves of outgoing pickings.

        :return: dict {chain key: shipment picking ids, most urgent first}
        """
        end_ids = self._walk_dest_chains(
            chain_key=chain_key,
            chain_end_selector=self._get_ship_move_ids,
            done=done,
        )
        # picking_id and the ordering fields are fetched by the walk and the
        # outgoing check: sorting costs no query
        return {
            key: self.browse(m_ids)
            .picking_id.sorted(key=lambda p: p._get_ship_sort_key())
            .ids
            for key, m_ids in end_ids.items()
        }

    @api.model
    def _get_ship_move_ids(self, moves):
        """Return the ids of the moves of outgoing pickings among ``moves``."""
        outgoing_ids = self.env["stock.picking"]._get_outgoing_picking_ids(
            set(moves.picking_id.ids)
        )
        return {move.id for move in moves if move.picking_id.id in outgoing_ids}

    def _walk_dest_chains(
        self,
        chain_key=None,
        chain_end_selector=None,
        include_last_moves=False,
        done=False,
    ):
        """Return the moves ending each chain starting from the moves.

        The moves are grouped in chains by ``chain_key``. From the moves of
        each chain, follow all the destination moves not
        done nor cancelled (only done or cancelled ones when ``done`` is set).
        A move ends its chain when ``chain_end_selector`` selects it, or when
        it has no destination and ``include_last_moves`` is set. A chain
        looping on itself stops without end move.

        The chains are walked together, one level at a time, reading only
        the fields needed: the number of queries depends on the depth of the
        chains, not on their number.

        :param chain_key: function returning the chain key of a move,
            defaults to the move id: each move is its own chain
        :param chain_end_selector: optional function called once per level
            with the moves reached, returning the ids of those ending their
            chain
        :param include_last_moves: keep the moves without destination as
            chain ends
        :return: dict {chain key: end move ids}, chains without end move are
            not in the dict
        """
        if not self or (not chain_end_selector and not include_last_moves):
            return {}  # nothing can be collected: skip all queries
        if chain_key is None:
            chain_key = attrgetter("id")
        to_follow = defaultdict(list)
        for move in self:
            to_follow[chain_key(move)].append(move.id)
        visited = defaultdict(set)
        end_ids = defaultdict(list)
        # the moves of the chain itself are not an end: checked from level 2
        last_candidates = {}
        while to_follow:
            origin_ids = {m_id for m_ids in to_follow.values() for m_id in m_ids}
            dests_by_origin = self.browse(origin_ids)._get_dests_by_origin_id(done=done)
            if include_last_moves:
                self._add_last_moves(last_candidates, dests_by_origin, end_ids)
            reached = self._get_reached_moves(to_follow, dests_by_origin, visited)
            end_move_ids = self._select_chain_ends(chain_end_selector, reached)
            to_follow = {}
            for key, dests in reached.items():
                next_ids = []
                for dest in dests:
                    if dest.id in end_move_ids:
                        end_ids[key].append(dest.id)
                    else:
                        next_ids.append(dest.id)
                if next_ids:
                    to_follow[key] = next_ids
            last_candidates = to_follow
        return dict(end_ids)

    @api.model
    def _get_reached_moves(self, to_follow, dests_by_origin, visited):
        """Return the destination moves not visited yet, by chain key."""
        reached = {}
        for key, move_ids in to_follow.items():
            dests = []
            for m_id in move_ids:
                for dest in dests_by_origin.get(m_id, []):
                    # a chain looping on itself stops
                    if dest.id not in visited[key]:
                        visited[key].add(dest.id)
                        dests.append(dest)
            reached[key] = dests
        return reached

    @api.model
    def _select_chain_ends(self, chain_end_selector, reached):
        """Return the ids of the reached moves selected as chain ends."""
        if not chain_end_selector:
            return set()
        # one call for all the chains: the number of queries stays per level
        return chain_end_selector(
            self.browse({dest.id for dests in reached.values() for dest in dests})
        )

    @api.model
    def _add_last_moves(self, to_follow, dests_by_origin, end_ids):
        """Add the followed moves without destination to ``end_ids``.

        A move whose destinations were all visited already is not added:
        its chain loops.
        """
        for key, move_ids in to_follow.items():
            for m_id in move_ids:
                if m_id not in dests_by_origin and m_id not in end_ids.get(key, ()):
                    end_ids[key].append(m_id)

    def _get_dests_by_origin_id(self, done=False):
        """Return the destination moves of each move.

        Only destination moves not done nor cancelled are considered (only
        done or cancelled ones when ``done`` is set).

        :return: dict {origin move id: destination moves, in move order}
        """
        state_operator = "in" if done else "not in"
        dests = self.search_fetch(
            [
                ("move_orig_ids", "in", self.ids),
                ("state", state_operator, ("cancel", "done")),
            ],
            ["move_orig_ids", "picking_id"],
            order=self._order,
        )
        dests_by_origin_id = defaultdict(list)
        for dest in dests:
            for origin_id in dest.move_orig_ids.ids:
                dests_by_origin_id[origin_id].append(dest)
        return dests_by_origin_id
