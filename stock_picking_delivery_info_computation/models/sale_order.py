# Copyright 2019 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_confirm(self):
        """Recompute picking volume when confirming sales order."""
        res = super(SaleOrder, self).action_confirm()
        self.mapped('picking_ids').action_calculate_volume()
        return res
