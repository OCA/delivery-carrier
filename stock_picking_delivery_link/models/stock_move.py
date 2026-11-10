# Copyright 2026 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from collections import defaultdict

from odoo import api, models


class StockMove(models.Model):
    _inherit = "stock.move"

    @api.model
    def _get_ship_id_by_chain(self, move_ids_by_chain, done=False):
        """Return the shipment reached by each chain of moves.

        From the moves of each chain, follow the first destination move (by
        move order) not done nor cancelled (only done or cancelled ones when
        ``done`` is set) until a move of an outgoing picking is reached.

        The chains are walked together, one level at a time, reading only
        the fields needed: the number of queries depends on the depth of the
        chains, not on their number.

        :param move_ids_by_chain: dict {chain key: ids of the moves to follow,
            in move order}
        :return: dict {chain key: shipment picking id}, chains without
            shipment are not in the dict
        """
        Picking = self.env["stock.picking"]
        to_follow = move_ids_by_chain
        visited = defaultdict(set)
        ship_ids = {}
        while to_follow:
            origin_ids = {m_id for m_ids in to_follow.values() for m_id in m_ids}
            dest_by_origin = self.browse(origin_ids)._get_first_dest_by_origin_id(
                done=done
            )
            reached = {}
            for key, move_ids in to_follow.items():
                # move_ids is a list, not a set: it is sorted by move order
                # and the first source move having a destination wins
                dest = next(
                    (
                        dest_by_origin[m_id]
                        for m_id in move_ids
                        if m_id in dest_by_origin
                    ),
                    None,
                )
                # a chain looping on itself stops without result
                if dest is None or dest.id in visited[key]:
                    continue
                visited[key].add(dest.id)
                reached[key] = dest
            outgoing_ids = Picking._get_outgoing_picking_ids(
                {dest.picking_id.id for dest in reached.values()}
            )
            to_follow = {}
            for key, dest in reached.items():
                if dest.picking_id.id in outgoing_ids:
                    ship_ids[key] = dest.picking_id.id
                else:
                    # a move without picking does not end the chain
                    to_follow[key] = [dest.id]
        return ship_ids

    def _get_first_dest_by_origin_id(self, done=False):
        """Return the first destination move of each move.

        Only destination moves not done nor cancelled are considered (only
        done or cancelled ones when ``done`` is set), in move order.

        :return: dict {origin move id: destination move}
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
        dest_by_origin_id = {}
        for dest in dests:
            for origin_id in dest.move_orig_ids.ids:
                dest_by_origin_id.setdefault(origin_id, dest)
        return dest_by_origin_id
