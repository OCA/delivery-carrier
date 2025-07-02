# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools import float_compare


class PackageType(models.Model):
    _inherit = "stock.package.type"

    is_base_weight_shipping_weight = fields.Boolean(
        string="Is shipping weight",
        help="""When flagged, the package type weight will be the package total weight.
         The product weight won't be added""",
    )

    @api.constrains("is_base_weight_shipping_weight", "base_weight")
    def _check_package_default_shipping_weight(self):
        """
        Ensure base_weight is non-negative if package uses base weight as shipping
        weight.
        """
        weight_uom = self.env[
            "product.template"
        ]._get_weight_uom_id_from_ir_config_parameter()
        for packaging in self.filtered(
            lambda pack: pack.is_base_weight_shipping_weight
        ):
            if (
                float_compare(
                    packaging.base_weight,
                    0,
                    precision_rounding=weight_uom.rounding,
                )
                < 0
            ):
                raise ValidationError(
                    _(
                        """Weight must be a positive or null value if Is shipping
                        weight is enabled."""
                    )
                )
