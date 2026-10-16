# Copyright 2026 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    restrict_zone_to_delivery_addresses = fields.Boolean(
        related="company_id.restrict_zone_to_delivery_addresses",
        readonly=False,
        string="Restrict Delivery Zone to Delivery Addresses",
    )
