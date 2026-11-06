# Copyright 2021 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from collections import defaultdict

from odoo import fields, models


def get_first_move_dest(moves, done=False):
    move_states = ("cancel", "done")
    for move in moves.move_dest_ids:
        if done and move.state in move_states:
            return move
        if not done and move.state not in move_states:
            return move


class StockPicking(models.Model):
    _inherit = "stock.picking"

    ship_picking_id = fields.Many2one(
        comodel_name="stock.picking",
        compute="_compute_ship_picking_data",
        string="Related delivery",
    )
    ship_carrier_id = fields.Many2one(
        comodel_name="delivery.carrier",
        compute="_compute_ship_picking_data",
        string="Related carrier",
    )

    def _compute_ship_picking_data(self):
        ship_by_picking = self._get_ship_by_picking_id()
        for picking in self:
            ship = ship_by_picking.get(picking._origin.id, self.browse())
            picking.ship_picking_id = ship
            picking.ship_carrier_id = ship.carrier_id

    def _get_ship_from_chain(self, done=False):
        """Returns the shipment related to the current operation."""
        self.ensure_one()
        return self._get_ship_by_picking_id(done=done).get(
            self._origin.id, self.browse()
        )

    def _get_ship_by_picking_id(self, done=False):
        """Return the shipments related to the operations, by picking id.

        From the moves of each picking, follow the first destination move
        (by move order) not done nor cancelled (only done or cancelled ones
        when ``done`` is set) until a move of an outgoing picking is reached.

        The chains of all the pickings are walked together, one level at a
        time, reading only the fields needed: the number of queries depends
        on the depth of the chains, not on the number of pickings.

        :return: dict {picking id: shipment}, pickings without shipment are
            not in the dict
        """
        # picking id -> ids of the moves to follow, in order
        to_follow = self._get_move_ids_by_picking_id()
        visited = defaultdict(set)
        ship_ids = {}
        while to_follow:
            origin_ids = {mid for mids in to_follow.values() for mid in mids}
            dest_by_origin = self._get_first_dest_by_origin_id(origin_ids, done=done)
            reached = {}
            for picking_id, move_ids in to_follow.items():
                dest = next(
                    (dest_by_origin[mid] for mid in move_ids if mid in dest_by_origin),
                    None,
                )
                # a chain looping on itself stops without result
                if dest is None or dest.id in visited[picking_id]:
                    continue
                visited[picking_id].add(dest.id)
                reached[picking_id] = dest
            outgoing_ids = self._get_outgoing_picking_ids(
                {dest.picking_id.id for dest in reached.values()}
            )
            to_follow = {}
            for picking_id, dest in reached.items():
                if dest.picking_id.id in outgoing_ids:
                    ship_ids[picking_id] = dest.picking_id.id
                else:
                    # a move without picking does not end the chain
                    to_follow[picking_id] = [dest.id]
        prefetch_ids = list(ship_ids.values())
        return {
            picking_id: self.browse(ship_id).with_prefetch(prefetch_ids)
            for picking_id, ship_id in ship_ids.items()
        }

    def _get_move_ids_by_picking_id(self):
        """Return the ids of the moves of the pickings, in move order."""
        Move = self.env["stock.move"]
        moves = Move.search_fetch(
            [("picking_id", "in", self._origin.ids)], ["picking_id"], order=Move._order
        )
        move_ids_by_picking_id = defaultdict(list)
        for move in moves:
            move_ids_by_picking_id[move.picking_id.id].append(move.id)
        return move_ids_by_picking_id

    def _get_first_dest_by_origin_id(self, origin_ids, done=False):
        """Return the first destination move of each origin move.

        Only destination moves not done nor cancelled are considered (only
        done or cancelled ones when ``done`` is set), in move order.

        :return: dict {origin move id: destination move}
        """
        Move = self.env["stock.move"]
        state_operator = "in" if done else "not in"
        dests = Move.search_fetch(
            [
                ("move_orig_ids", "in", list(origin_ids)),
                ("state", state_operator, ("cancel", "done")),
            ],
            ["move_orig_ids", "picking_id"],
            order=Move._order,
        )
        dest_by_origin_id = {}
        for dest in dests:
            for origin_id in dest.move_orig_ids.ids:
                dest_by_origin_id.setdefault(origin_id, dest)
        return dest_by_origin_id

    def _get_outgoing_picking_ids(self, picking_ids):
        """Return the ids of the outgoing pickings among ``picking_ids``."""
        outgoing = self.search(
            [
                ("id", "in", list(picking_ids - {False})),
                ("picking_type_id.code", "=", "outgoing"),
            ]
        )
        return set(outgoing.ids)

    def _pre_put_in_pack_hook(self, move_line_ids):
        res = super()._pre_put_in_pack_hook(move_line_ids)
        if not res:
            if (
                self.picking_type_id.set_delivery_package_type_on_put_in_pack
                and self.ship_carrier_id
            ):
                return self._set_delivery_package_type()
        else:
            return res

    def _set_delivery_package_type(self, batch_pack=False):
        """
        As we want to filter package types on carrier even on internal
        pickings, we pass the delivery type to the context from
        the related carrier taken from the delivery picking.
        """
        self.ensure_one()
        res = super()._set_delivery_package_type(batch_pack=batch_pack)
        context = res.get("context", self.env.context)
        # We don't want to overwrite the value set if carrier_id is filled in
        # and not ship_carrier_id (e.g.: one step delivery or propagate_carrier
        # is enabled)
        if self.ship_carrier_id.delivery_type:
            context = dict(
                context,
                current_package_carrier_type=self.ship_carrier_id.delivery_type,
            )
        # As we pass the `delivery_type` ('fixed' or 'base_on_rule' by default) in a
        # key which corresponds to the `package_carrier_type` ('none' to default), we
        # make a conversion. No conversion needed for other carriers as the
        # `delivery_type` and`package_carrier_type` will be the same in these cases.
        if context["current_package_carrier_type"] in ["fixed", "base_on_rule"]:
            context = dict(context, current_package_carrier_type="none")
        res["context"] = context
        return res
