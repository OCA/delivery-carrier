# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    delivery_cutoff_minutes = fields.Integer(
        string="Departure Cutoff (minutes)",
        related="company_id.delivery_cutoff_minutes",
        readonly=False,
        help="Minimum lead time (in minutes) before a scheduled departure "
        "within which a slot is considered unreachable. Orders confirmed "
        "within this window are rolled to the next available slot.",
    )
