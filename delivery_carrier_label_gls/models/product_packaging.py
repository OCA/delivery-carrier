# -*- coding: utf-8 -*-
# Copyright 2021 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ProductPackaging(models.Model):
    _inherit = "product.packaging"

    package_carrier_type = fields.Selection(selection_add=[("gls", "Gls")])
