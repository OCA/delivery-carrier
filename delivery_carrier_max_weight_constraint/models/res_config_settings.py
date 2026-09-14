# Copyright 2022 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    delivery_carrier_strict_weight_package = fields.Boolean(
        related="company_id.delivery_carrier_strict_weight_package",
        readonly=False,
    )
