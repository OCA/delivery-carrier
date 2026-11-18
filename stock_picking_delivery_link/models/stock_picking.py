# Copyright 2021 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from collections import defaultdict

from odoo import api, fields, models


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

        See ``stock.move._get_ship_id_by_chain``: each picking is a chain
        starting from its own moves.

        :return: dict {picking id: shipment}, pickings without shipment are
            not in the dict
        """
        ship_ids = self.env["stock.move"]._get_ship_id_by_chain(
            self._get_move_ids_by_picking_id(), done=done
        )
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

    @api.model
    def _get_outgoing_picking_ids(self, picking_ids):
        """Return the ids of the outgoing pickings among ``picking_ids``."""
        outgoing = self.search(
            [
                ("id", "in", list(picking_ids - {False})),
                ("picking_type_id.code", "=", "outgoing"),
            ]
        )
        return set(outgoing.ids)
