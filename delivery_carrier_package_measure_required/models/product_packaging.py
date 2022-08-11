# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import fields, models


class ProductPackaging(models.Model):
    _inherit = "product.packaging"

    package_height_required = fields.Boolean(string="Height required")
    package_length_required = fields.Boolean(string="Length required")
    package_weight_required = fields.Boolean(string="Weight required")
    package_width_required = fields.Boolean(string="Width required")
