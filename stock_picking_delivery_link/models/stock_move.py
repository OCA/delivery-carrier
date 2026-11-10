# Copyright 2026 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from collections import defaultdict

from odoo import api, models


class StockMove(models.Model):
    _inherit = "stock.move"

    @api.model
    def _get_ship_ids_by_chain(self, move_ids_by_chain, done=False):
        """Return the shipments reached by each chain of moves.

        From the moves of each chain, follow the destination moves not done
        nor cancelled (only done or cancelled ones when ``done`` is set)
        until moves of outgoing pickings are reached.

        Two results are given for each chain:

        - the first shipment: reached by following only the first destination
          move (by move order) at each level
        - all the shipments: reached by following all the destination moves

        The chains are walked together, one level at a time, reading only
        the fields needed: the number of queries depends on the depth of the
        chains, not on their number.

        :param move_ids_by_chain: dict {chain key: ids of the moves to follow,
            in move order}
        :return: tuple of dicts ({chain key: first shipment picking id},
            {chain key: list of all shipment picking ids}), chains without
            shipment are not in the dicts
        """
        Picking = self.env["stock.picking"]
        to_follow = {key: list(m_ids) for key, m_ids in move_ids_by_chain.items()}
        # Last move reached by following only the first destination move:
        # None before the first level, removed once the path ends.
        first_path = dict.fromkeys(to_follow)
        first_path_visited = defaultdict(set)
        visited = defaultdict(set)
        first_ship_ids = {}
        ship_ids = defaultdict(list)
        while to_follow:
            origin_ids = {m_id for m_ids in to_follow.values() for m_id in m_ids}
            dests_by_origin = self.browse(origin_ids)._get_dests_by_origin_id(
                done=done
            )
            reached = {}
            first_reached = {}
            for key, move_ids in to_follow.items():
                # move_ids is a list, not a set: it is sorted by move order
                dests = []
                for m_id in move_ids:
                    for dest in dests_by_origin.get(m_id, []):
                        # a chain looping on itself stops
                        if dest.id not in visited[key]:
                            visited[key].add(dest.id)
                            dests.append(dest)
                reached[key] = dests
                if key in first_path:
                    first_dest = self._get_first_path_dest(
                        first_path[key], move_ids, dests_by_origin
                    )
                    if first_dest and first_dest.id not in first_path_visited[key]:
                        first_path_visited[key].add(first_dest.id)
                        first_reached[key] = first_dest
                    else:
                        del first_path[key]
            outgoing_ids = Picking._get_outgoing_picking_ids(
                {dest.picking_id.id for dests in reached.values() for dest in dests}
                | {dest.picking_id.id for dest in first_reached.values()}
            )
            to_follow = {}
            for key, dests in reached.items():
                next_ids = []
                for dest in dests:
                    if dest.picking_id.id in outgoing_ids:
                        if dest.picking_id.id not in ship_ids[key]:
                            ship_ids[key].append(dest.picking_id.id)
                    else:
                        # a move without picking does not end the chain
                        next_ids.append(dest.id)
                first_dest = first_reached.get(key)
                if first_dest and first_dest.picking_id.id in outgoing_ids:
                    first_ship_ids[key] = first_dest.picking_id.id
                    del first_path[key]
                elif first_dest:
                    first_path[key] = first_dest.id
                    # already reached by another branch: follow it anyway
                    if first_dest.id not in next_ids:
                        next_ids.append(first_dest.id)
                if next_ids:
                    to_follow[key] = next_ids
        return first_ship_ids, dict(ship_ids)

    @api.model
    def _get_first_path_dest(self, path_move_id, move_ids, dests_by_origin):
        """Return the next move of the path following only first destinations.

        :param path_move_id: last move of the path, None to start from the
            first move of ``move_ids`` having a destination
        """
        source_ids = move_ids if path_move_id is None else [path_move_id]
        return next(
            (
                dests_by_origin[m_id][0]
                for m_id in source_ids
                if m_id in dests_by_origin
            ),
            None,
        )

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
