# Copyright 2026 NICO SOLUTIONS - Nils Coenen
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import models


class ResPartner(models.Model):
    _inherit = "res.partner"

    def write(self, vals):
        res = super().write(vals)
        if "delivery_schedule_ids" in vals:
            pickings = self.env["stock.picking"].search(
                [
                    ("partner_id", "in", self.ids),
                    ("state", "not in", ["done", "cancel"]),
                ]
            )
            pickings._compute_partner_delivery_schedule_warning()
        return res
