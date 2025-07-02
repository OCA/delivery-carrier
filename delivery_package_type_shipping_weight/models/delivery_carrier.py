from odoo import models


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    def _get_packages_from_order(self, order, default_package_type):
        # Exclude product weight if package type uses base weight.
        if default_package_type.is_base_weight_shipping_weight:
            return super()._get_packages_from_order(
                order.with_context(ignore_product_weight=True),
                default_package_type,
            )
        return super()._get_packages_from_order(order, default_package_type)

    def _get_packages_from_picking(self, picking, default_package_type):
        # Exclude product weight if package type uses base weight.
        if default_package_type.is_base_weight_shipping_weight:
            return super()._get_packages_from_picking(
                picking.with_context(ignore_product_weight=True),
                default_package_type,
            )
        return super()._get_packages_from_picking(picking, default_package_type)
