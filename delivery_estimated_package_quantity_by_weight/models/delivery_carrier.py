# Copyright 2021 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    maximum_weight_per_package = fields.Float(string="Maximum weight per package")
    weight_uom_name = fields.Char(
        string="Weight unit of measure label", compute="_compute_weight_uom_name"
    )

    def _compute_weight_uom_name(self):
        weight_uom_name = self.env[
            "product.template"
        ]._get_weight_uom_name_from_ir_config_parameter()
        for rec in self:
            rec.weight_uom_name = weight_uom_name
