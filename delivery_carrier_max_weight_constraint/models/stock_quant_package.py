# coding: utf-8
# Copyright 2021 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _, api, models
from odoo.exceptions import ValidationError


class StockQuantPackage(models.Model):
    _inherit = "stock.quant.package"

    @api.constrains("shipping_weight", "packaging_id")
    def _constrain_shipping_weight(self):
        for package in self:
            max_weight = package.packaging_id.max_weight
            if max_weight and package.shipping_weight > max_weight:
                msg = _(
                    "The shipping weight of package %s cannot exceed "
                    "the maximum weight %s configured on its packaging type %s."
                )
                type_name = package.packaging_id.name
                raise ValidationError(msg % (package.name, max_weight, type_name))
