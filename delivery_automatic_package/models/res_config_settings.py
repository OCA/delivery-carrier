# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):

    _inherit = "res.config.settings"

    automatic_package_creation_at_delivery_default = fields.Boolean(
        related="company_id.automatic_package_creation_at_delivery_default",
        readonly=False,
    )
