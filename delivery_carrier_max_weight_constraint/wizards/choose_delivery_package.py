# Copyright 2022 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _, api, models
from odoo.exceptions import ValidationError


class ChooseDeliveryPackage(models.TransientModel):
    _inherit = "choose.delivery.package"

    @api.constrains("delivery_package_type_id", "shipping_weight")
    def _check_strict_weight_package(self):
        for package in self:
            if (
                package.delivery_package_type_id.is_strict_weight
                and package.delivery_package_type_id.max_weight
                and package.shipping_weight
                > package.delivery_package_type_id.max_weight
            ):
                error_msg = _(
                    "The weight of your package is higher than the maximum "
                    "weight authorized for this package type. Please choose "
                    "another package type."
                )
                raise ValidationError(error_msg)
