# Copyright 2021 Camptocamp
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def action_open_delivery_wizard(self):
        carrier_lines = self.order_line.filtered(lambda self: self.carrier_id)
        if carrier_lines:
            message = """
                Shipping method is managed at line level, please update the
                information manually in every line
                """
            raise UserError(message)
        return super().action_open_delivery_wizard()
