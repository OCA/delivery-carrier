# Copyright 2012 Camptocamp SA
# Author: Guewen Baconnier
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class StockMove(models.Model):
    _inherit = "stock.move"

    def write(self, values):
        write_result = super(StockMove, self).write(values)
        if values.get("state") == "done":
            done_pickings = self.mapped("picking_id").filtered(
                lambda sp: sp.state == "done"
            )
            if done_pickings:
                done_pickings.generate_carrier_files()
        return write_result
