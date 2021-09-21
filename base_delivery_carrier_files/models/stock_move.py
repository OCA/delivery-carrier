# Copyright 2012 Camptocamp SA
# Author: Guewen Baconnier
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class StockMove(models.Model):
    _inherit = "stock.move"

    def write(self, values):
        res = super().write(values)
        if values.get("state") and values["state"] == "done":
            picking_ids = list(map(lambda p: p.id, self.mapped("picking_id")))
            done_pickings = self.env["stock.picking"].search(
                [("id", "in", picking_ids), ("state", "=", "done")]
            )
            if done_pickings:
                done_pickings.generate_carrier_files()
        return res
