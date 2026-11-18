# Copyright 2026 arielbarreiros96 (https://github.com/arielbarreiros96)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl)

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    sendcloud_return_picking_start_date = fields.Date(
        string="Return Operations From",
        help="Returns created in Sendcloud before this date do not get a warehouse "
        "operation unless they already have one. Leave empty to process every return.",
    )
