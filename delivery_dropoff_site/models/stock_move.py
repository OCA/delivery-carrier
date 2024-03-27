# Copyright (C) 2018 - Today: GRAP (http://www.grap.coop)
# @author: Sylvain LE GAL (https://twitter.com/legalsylvain)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class StockMove(models.Model):
    _inherit = "stock.move"

    final_shipping_partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Final Recipient",
        help="It is the partner that will pick up the parcel " "in the dropoff site.",
    )

    def _get_new_picking_values(self):
        res = super()._get_new_picking_values()
        res.update(
            {
                "final_shipping_partner_id": self.final_shipping_partner_id.id,
            }
        )
        return res
