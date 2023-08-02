# Copyright 2023 Cetmix OÜ - Andrey Solodovnikov
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class DeliverPriceRule(models.Model):
    _inherit = "delivery.price.rule"

    exclude_product_domain = fields.Char(string="Ecxlude Products")
