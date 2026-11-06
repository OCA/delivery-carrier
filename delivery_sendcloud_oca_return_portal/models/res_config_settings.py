# Copyright 2026 arielbarreiros96 (https://github.com/arielbarreiros96)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl)

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    sendcloud_return_picking_start_date = fields.Date(
        related="company_id.sendcloud_return_picking_start_date", readonly=False
    )
