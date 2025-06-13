from odoo import models


class ChooseDeliveryPackage(models.TransientModel):
    _inherit = "choose.delivery.package"

    def _compute_shipping_weight(self):
        # Calculate shipping weight using base weight or product move lines.
        base_weight_shipping = self.filtered(
            lambda pkg: pkg.delivery_package_type_id.is_base_weight_shipping_weight
        )
        other_shipping = self - base_weight_shipping
        result = super(ChooseDeliveryPackage, other_shipping)._compute_shipping_weight()
        for choose_package in base_weight_shipping:
            choose_package.shipping_weight = (
                choose_package.delivery_package_type_id.base_weight or 0.0
            )
        return result
