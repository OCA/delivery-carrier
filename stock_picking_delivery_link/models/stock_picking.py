# Copyright 2021 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

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
        for picking in self:
            ship = picking._get_ship_from_chain()
            picking.ship_picking_id = ship
            picking.ship_carrier_id = ship.carrier_id

    def _get_ship_from_chain(self, done=False):
        """Returns the shipment related to the current operation."""
        move_dest = get_first_move_dest(self.move_ids, done=done)
        while move_dest:
            picking = move_dest.picking_id
            if picking.picking_type_id.code == "outgoing":
                return picking
            move_dest = get_first_move_dest(move_dest, done=done)
        # Should return an empty record if we reach this line
        return self.browse()

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
        # and not ship_carrier_id (e.g.: one step delivery or propagate_carrier is enabled)
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
