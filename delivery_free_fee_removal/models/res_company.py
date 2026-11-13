# Copyright 2026 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    report_saleorder_hide_free_delivery_lines = fields.Boolean(
        string="Hide free delivery lines in sale order report",
        default=True,
    )
