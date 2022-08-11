# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import fields, models


class ChooseDeliveryPackage(models.TransientModel):
    _inherit = "choose.delivery.package"

    pick_name = fields.Char(related="picking_id.name")

    def _default_dimension_uom_id(self):
        val = self.env["product.template"]._get_length_uom_id_from_ir_config_parameter()
        return val

    package_height = fields.Integer()
    package_length = fields.Integer()
    package_width = fields.Integer()
    dimension_uom_id = fields.Many2one(
        "uom.uom",
        default=lambda self: self._default_dimension_uom_id(),
    )
    dimension_uom_name = fields.Char(related="dimension_uom_id.name")
    package_height_required = fields.Boolean(
        related="delivery_packaging_id.package_height_required"
    )
    package_length_required = fields.Boolean(
        related="delivery_packaging_id.package_length_required"
    )
    package_weight_required = fields.Boolean(
        related="delivery_packaging_id.package_weight_required"
    )
    package_width_required = fields.Boolean(
        related="delivery_packaging_id.package_width_required"
    )
