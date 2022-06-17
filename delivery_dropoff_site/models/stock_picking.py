# Copyright (C) 2018 - Today: GRAP (http://www.grap.coop)
# @author: Sylvain LE GAL (https://twitter.com/legalsylvain)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    final_shipping_partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Final Recipient",
        help="It is the partner that will pick up the parcel " "in the dropoff site.",
    )
