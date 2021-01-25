# Copyright 2021 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    send_delivery_confirmation = fields.Boolean(
        string="Send Delivery Confirmation",
        related="company_id.send_delivery_confirmation",
        readonly=False,
    )
