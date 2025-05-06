from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    delivery_set_default_package = fields.Boolean(
        related="company_id.delivery_set_default_package",
        readonly=False,
    )
