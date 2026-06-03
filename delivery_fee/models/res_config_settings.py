# Copyright 2026 Moduon
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
from odoo import fields, models


class ResConfigSetting(models.TransientModel):
    _inherit = "res.config.settings"

    one_delivery_fee_by_sale_order = fields.Boolean(
        related="company_id.one_delivery_fee_by_sale_order",
        readonly=False,
    )
    one_delivery_fee_by_commercial_partner_day = fields.Boolean(
        related="company_id.one_delivery_fee_by_commercial_partner_day",
        readonly=False,
    )
