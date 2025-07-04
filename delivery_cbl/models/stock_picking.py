# Copyright 2025 Manuel Regidor <manuel.regidor@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    cbl_confirmed = fields.Boolean(readonly=True, default=False)

    def cbl_confirm_shipment(self):
        self.ensure_one()
        if (
            self.delivery_type == "cbl"
            and self.carrier_tracking_ref
            and not self.cbl_confirmed
        ):
            self.carrier_id.cbl_confirm_shipment(self)

    def action_open_wizard_confirm_cbl_pickings(self):
        return {
            "type": "ir.actions.act_window",
            "name": "Confirm CBL pickings",
            "res_model": "wizard.confirm.cbl.pickings",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_picking_ids": self.ids,
            },
        }
