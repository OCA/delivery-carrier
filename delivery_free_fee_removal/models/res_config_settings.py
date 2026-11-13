# Copyright 2026 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    report_saleorder_hide_free_delivery_lines = fields.Boolean(
        related="company_id.report_saleorder_hide_free_delivery_lines",
        readonly=False,
    )
