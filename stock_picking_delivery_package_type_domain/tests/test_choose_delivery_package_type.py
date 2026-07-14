# Copyright 2024 ACSONE SA/NV (https://www.acsone.eu)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo.addons.base.tests.common import BaseCommon

from .common import CommonChooseDeliveryPackage


class TestChooseDeliveryPackageType(CommonChooseDeliveryPackage, BaseCommon):
    def _confirm_ship(self):
        sale = self._create_sale()
        sale.action_confirm()
        self.assertTrue(sale.picking_ids)
        return sale.picking_ids

    def _make_wizard(self, picking):
        return (
            self.env["choose.delivery.package"]
            .with_context(default_picking_id=picking.id)
            .create({})
        )

    def test_carrier_option_enabled_type_test(self):
        """Carrier + option enabled + delivery type "test" => domain on "test"."""
        picking = self._confirm_ship()
        picking.picking_type_id.filter_package_type_on_put_in_pack = True
        wizard = self._make_wizard(picking)
        self.assertEqual(
            [("package_carrier_type", "=", "test")], wizard.package_type_domain
        )

    def test_carrier_option_enabled_type_converted(self):
        """Carrier + option enabled + fixed/base_on_rule => domain on "none"."""
        picking = self._confirm_ship()
        picking.picking_type_id.filter_package_type_on_put_in_pack = True
        for delivery_type in ("fixed", "base_on_rule"):
            picking.carrier_id.delivery_type = delivery_type
            wizard = self._make_wizard(picking)
            self.assertEqual(
                [("package_carrier_type", "=", "none")],
                wizard.package_type_domain,
                delivery_type,
            )

    def test_carrier_option_disabled(self):
        """Carrier + option disabled => no domain."""
        picking = self._confirm_ship()
        picking.picking_type_id.filter_package_type_on_put_in_pack = False
        wizard = self._make_wizard(picking)
        self.assertFalse(wizard.package_type_domain)

    def test_no_carrier_option_enabled(self):
        """No carrier + option enabled => domain on False."""
        picking = self._confirm_ship()
        picking.carrier_id = False
        picking.picking_type_id.filter_package_type_on_put_in_pack = True
        wizard = self._make_wizard(picking)
        self.assertEqual(
            [("package_carrier_type", "=", False)], wizard.package_type_domain
        )

    def test_no_carrier_option_disabled(self):
        """No carrier + option disabled => no domain."""
        picking = self._confirm_ship()
        picking.carrier_id = False
        picking.picking_type_id.filter_package_type_on_put_in_pack = False
        wizard = self._make_wizard(picking)
        self.assertFalse(wizard.package_type_domain)
