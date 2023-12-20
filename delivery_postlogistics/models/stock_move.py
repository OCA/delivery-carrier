# Copyright 2013 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class StockMove(models.Model):
    _inherit = "stock.move"

    def _get_new_picking_values(self):
        vals = super()._get_new_picking_values()

        order_commitment_dates = [
            date
            for date in self.sale_line_id.order_id.mapped("commitment_date")
            if date
        ]
        if order_commitment_dates:
            user_time = fields.Datetime.context_timestamp(
                self, max(order_commitment_dates)
            ).date()
            vals["delivery_fixed_date"] = user_time
        return vals
