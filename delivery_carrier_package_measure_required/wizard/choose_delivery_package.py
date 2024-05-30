# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import api, fields, models


class ChooseDeliveryPackage(models.TransientModel):
    _inherit = "choose.delivery.package"

    @api.depends("delivery_package_type_id")
    def _compute_dimension_uom_name(self):
        length_uom_id = self.env[
            "product.template"
        ]._get_length_uom_id_from_ir_config_parameter()
        for package in self:
            package.dimension_uom_name = length_uom_id.name

    @api.depends("delivery_package_type_id")
    def _compute_dimension(self):
        for package in self:
            package.package_length = (
                package.delivery_package_type_id.packaging_length or 0
            )
            package.package_width = package.delivery_package_type_id.width or 0
            package.package_height = package.delivery_package_type_id.height or 0

    package_length = fields.Integer(
        compute="_compute_dimension", store=True, readonly=False
    )
    package_width = fields.Integer(
        compute="_compute_dimension", store=True, readonly=False
    )
    package_height = fields.Integer(
        compute="_compute_dimension", store=True, readonly=False
    )
    dimension_uom_name = fields.Char(compute="_compute_dimension_uom_name")
    package_height_required = fields.Boolean(
        related="delivery_package_type_id.package_height_required"
    )
    package_length_required = fields.Boolean(
        related="delivery_package_type_id.package_length_required"
    )
    package_width_required = fields.Boolean(
        related="delivery_package_type_id.package_width_required"
    )
    package_weight_required = fields.Boolean(
        related="delivery_package_type_id.package_weight_required"
    )

    def action_put_in_pack(self):
        self = self.with_context(
            choose_delivery_package_length=self.package_length,
            choose_delivery_package_width=self.package_width,
            choose_delivery_package_height=self.package_height,
            choose_delivery_package_pack_weight=self.shipping_weight,
        )
        return super().action_put_in_pack()
