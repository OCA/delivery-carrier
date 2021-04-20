# Copyright 2012 Camptocamp SA
# Author: Guewen Baconnier
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class DeliveryCarrierFileGenerate(models.TransientModel):

    _name = "delivery.carrier.file.generate"
    _description = "Wizard to generate delivery carrier files"

    @api.model
    def _get_pickings(self):
        context = self.env.context
        if context.get("active_model") == "stock.picking" and context.get("active_ids"):
            return self.env["stock.picking"].browse(context["active_ids"])

    def action_generate(self):
        """
        Call the creation of the delivery carrier files
        """
        if not self.pickings:
            raise UserError(_("No delivery orders selected"))
        self.pickings.generate_carrier_files(auto=False, recreate=self.recreate)
        return {"type": "ir.actions.act_window_close"}

    pickings = fields.Many2many(
        "stock.picking",
        string="Delivery Orders",
        default=_get_pickings,
    )
    recreate = fields.Boolean(
        "Recreate files",
        help=(
            "If this option is used, new files will be generated "
            "for selected picking even if they already had one.\n"
            "By default, delivery orders with existing file will be "
            "skipped."
        ),
    )
