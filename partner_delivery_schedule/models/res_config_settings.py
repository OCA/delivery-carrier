# Copyright 2026 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    delivery_schedule_departure_horizon = fields.Integer(
        related="company_id.delivery_schedule_departure_horizon",
        readonly=False,
        string="Delivery Departure Horizon (days)",
    )
