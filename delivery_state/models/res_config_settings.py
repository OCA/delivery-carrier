# Copyright 2022 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    delivery_state_delivered_email_validation = fields.Boolean(
        related="company_id.delivery_state_delivered_email_validation", readonly=False
    )
    delivery_state_delivered_mail_template_id = fields.Many2one(
        related="company_id.delivery_state_delivered_mail_template_id", readonly=False
    )
