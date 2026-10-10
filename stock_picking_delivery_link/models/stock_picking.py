# Copyright 2021 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models
from odoo.tools import SQL


def get_first_move_dest(moves, done=False):
    """Return the first destination move of ``moves`` matching ``done``.

    Kept for backward compatibility: the chain is now resolved in SQL by
    ``stock.picking._get_ships_from_chain``.
    """
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
        ships = self._get_ships_from_chain()
        for picking in self:
            ship = ships.get(picking._origin.id, self.browse())
            picking.ship_picking_id = ship
            picking.ship_carrier_id = ship.carrier_id

    def _get_ship_from_chain(self, done=False):
        """Returns the shipment related to the current operation."""
        self.ensure_one()
        return self._get_ships_from_chain(done=done).get(self._origin.id, self.browse())

    def _get_ships_from_chain(self, done=False):
        """Return the shipments related to the operations, by picking id.

        From the moves of each picking, follow the first destination move
        (by ``sequence, id``) not done nor cancelled (only done or cancelled
        ones when ``done`` is set) until a move of an outgoing picking is
        reached. The whole recordset is resolved with a single query,
        whatever the depth of the chains. Destination moves of companies not
        allowed in the environment are ignored, as the ORM record rules do,
        and a chain looping on itself stops without result.

        :param done: follow done or cancelled destination moves instead
        :return: dict {picking id: shipment picking}, pickings without
            shipment are not in the dict
        """
        picking_ids = self._origin.ids
        if not picking_ids:
            return {}
        self.env["stock.move"].flush_model(
            [
                "company_id",
                "move_dest_ids",
                "move_orig_ids",
                "picking_id",
                "sequence",
                "state",
            ]
        )
        self.env["stock.picking"].flush_model(["picking_type_id"])
        self.env["stock.picking.type"].flush_model(["code"])
        rows = self.env.execute_query(
            self._get_ships_from_chain_query(picking_ids, done=done)
        )
        ship_ids = [ship_id for __, ship_id in rows]
        return {
            picking_id: self.browse(ship_id).with_prefetch(ship_ids)
            for picking_id, ship_id in rows
        }

    def _get_ships_from_chain_query(self, picking_ids, done=False):
        """Build the recursive query resolving the shipments of pickings."""
        if done:
            dest_state = SQL("dm.state IN ('done', 'cancel')")
        else:
            dest_state = SQL("dm.state NOT IN ('done', 'cancel')")
        if self.env.su:
            move_company = dest_company = SQL("TRUE")
        else:
            company_ids = self.env.companies.ids
            move_company = SQL("m.company_id = ANY(%s)", company_ids)
            dest_company = SQL("dm.company_id = ANY(%s)", company_ids)
        return SQL(
            """
            -- One row per step of the chain of each source picking:
            -- the move reached, its picking and the code of its type.
            WITH RECURSIVE chain AS (
                -- First step: from the moves of the source picking.
                SELECT p.id AS src_picking_id,
                       d.move_id,
                       dp.id AS picking_id,
                       pt.code,
                       -- moves visited so far, to detect cycles
                       ARRAY[d.move_id] AS path
                  FROM stock_picking p
                  CROSS JOIN LATERAL (
                      -- First eligible destination move, in the order the
                      -- ORM reads picking.move_ids.move_dest_ids: source
                      -- moves by sequence, id, then their destination moves
                      -- by sequence, id.
                      SELECT dm.id AS move_id, dm.picking_id
                        FROM stock_move m
                        JOIN stock_move_move_rel r ON r.move_orig_id = m.id
                        JOIN stock_move dm ON dm.id = r.move_dest_id
                       WHERE m.picking_id = p.id
                         AND %(move_company)s
                         AND %(dest_state)s
                         AND %(dest_company)s
                       ORDER BY m.sequence, m.id, dm.sequence, dm.id
                       LIMIT 1
                  ) d
                  -- LEFT JOIN: a move without picking does not end the
                  -- chain, it is followed like any other move.
                  LEFT JOIN stock_picking dp ON dp.id = d.picking_id
                  LEFT JOIN stock_picking_type pt ON pt.id = dp.picking_type_id
                 WHERE p.id = ANY(%(picking_ids)s)
              UNION ALL
                -- Next steps: from the move reached at the previous step.
                SELECT c.src_picking_id,
                       n.move_id,
                       dp.id,
                       pt.code,
                       c.path || n.move_id
                  FROM chain c
                  CROSS JOIN LATERAL (
                      -- Only the first eligible destination move is
                      -- followed: no backtracking to the other branches.
                      SELECT dm.id AS move_id, dm.picking_id
                        FROM stock_move_move_rel r
                        JOIN stock_move dm ON dm.id = r.move_dest_id
                       WHERE r.move_orig_id = c.move_id
                         AND %(dest_state)s
                         AND %(dest_company)s
                       ORDER BY dm.sequence, dm.id
                       LIMIT 1
                  ) n
                  LEFT JOIN stock_picking dp ON dp.id = n.picking_id
                  LEFT JOIN stock_picking_type pt ON pt.id = dp.picking_type_id
                 -- Stop once a delivery is reached; IS DISTINCT FROM keeps
                 -- going when the code is NULL (move without picking).
                 WHERE c.code IS DISTINCT FROM 'outgoing'
                   -- Stop on a move already visited: the chain loops.
                   AND NOT n.move_id = ANY(c.path)
            )
            -- The delivery is the outgoing picking reached, at most one per
            -- source picking since the chain stops there.
            SELECT src_picking_id, picking_id
              FROM chain
             WHERE code = 'outgoing'
            """,
            picking_ids=picking_ids,
            move_company=move_company,
            dest_state=dest_state,
            dest_company=dest_company,
        )
