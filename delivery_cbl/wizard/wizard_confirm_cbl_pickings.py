# Copyright 2025 Ángel Rivas <angel.rivas@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class WizardConfirmCblPickings(models.TransientModel):
    _name = "wizard.confirm.cbl.pickings"
    _description = "Wizard to Confirm CBL pickings"

    picking_ids = fields.Many2many("stock.picking")

    def default_get(self, fields):
        res = super().default_get(fields)
        picking_ids = self.env.context.get("default_picking_ids", [])
        pickings = self.env["stock.picking"].browse(picking_ids)
        filtered_pickings = pickings.filtered(
            lambda picking: picking.carrier_tracking_ref
            and not picking.cbl_confirmed
            and picking.delivery_type == "cbl"
            and picking.state == "done"
        )
        res["picking_ids"] = [(4, id) for id in filtered_pickings.ids]
        return res

    def action_confirm_cbl_pickings(self):
        carriers = self.picking_ids.mapped("carrier_id").filtered(
            lambda c: c.delivery_type == "cbl" and c.cbl_needs_confirmation
        )
        for carrier in carriers:
            pickings = self.picking_ids.filtered(
                lambda p, carrier=carrier: p.carrier_id == carrier
                and p.carrier_tracking_ref
                and not p.cbl_confirmed
                and p.delivery_type == "cbl"
                and p.state == "done"
            )
            if pickings:
                carrier.cbl_confirm_shipment(pickings)

        return {"type": "ir.actions.act_window_close"}
