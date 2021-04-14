# Copyright 2013-2016 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class StockMove(models.Model):
    _inherit = "stock.move"

    def _get_new_picking_values(self):
        vals = super(StockMove, self)._get_new_picking_values()

        order_commitment_date = (
            self.sale_line_id and self.sale_line_id.order_id.commitment_date
        )

        if order_commitment_date:
            user_time = fields.Datetime.context_timestamp(
                self, order_commitment_date
            ).date()
            vals["delivery_fixed_date"] = user_time
        return vals
