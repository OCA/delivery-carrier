from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    delivery_set_default_package = fields.Boolean(
        string="Default Packages",
        default=True,
    )
