# Copyright 2024 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    sale_auto_add_delivery_line = fields.Boolean(
        "Refresh shipping cost line automatically",
    )
    sale_refresh_delivery_after_picking = fields.Boolean(
        "Refresh delivery after picking automatically",
    )
    sale_auto_void_delivery_line = fields.Boolean(
        "Void delivery lines automatically",
    )
