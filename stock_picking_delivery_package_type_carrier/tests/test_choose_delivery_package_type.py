# Copyright 2026 Camptocamp SA (https://www.camptocamp.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo import Command

from odoo.addons.base.tests.common import BaseCommon
from odoo.addons.stock_picking_delivery_package_type_domain.tests.common import (
    CommonChooseDeliveryPackage,
)


class TestChooseDeliveryPackageType(CommonChooseDeliveryPackage, BaseCommon):
    def _confirm_ship(self):
        sale = self._create_sale()
        sale.action_confirm()
        self.assertTrue(sale.picking_ids)
        picking = sale.picking_ids
        picking.picking_type_id.filter_package_type_on_put_in_pack = True
        return picking

    def _make_wizard(self, picking):
        return (
            self.env["choose.delivery.package"]
            .with_context(default_picking_id=picking.id)
            .create({})
        )

    def test_domain_gets_correct_package_type(self):
        picking = self._confirm_ship()
        carrier = picking.carrier_id
        wizard = self._make_wizard(picking)
        self.assertEqual(
            wizard.package_type_domain,
            [
                "&",
                ("package_carrier_type", "=", carrier.delivery_type),
                "|",
                ("allowed_package_carrier_ids", "=", False),
                ("allowed_package_carrier_ids", "in", carrier.ids),
            ],
        )

    def test_domain_excludes_package_types_of_other_carriers(self):
        picking = self._confirm_ship()
        carrier = picking.carrier_id

        # package type selectable for this picking
        matching_type = self.env["stock.package.type"].create(
            {
                "name": "Type Matching Carrier",
                "package_carrier_type": carrier.delivery_type,
                "allowed_package_carrier_ids": [Command.set(carrier.ids)],
            }
        )

        # same carrier type with different dedicated carrier must be excluded
        other_carrier = self.env["delivery.carrier"].create(
            {
                "name": "Other Test Carrier",
                "delivery_type": carrier.delivery_type,
                "product_id": self.product_delivery.id,
            }
        )
        excluded_type = self.env["stock.package.type"].create(
            {
                "name": "Type Other Carrier",
                "package_carrier_type": carrier.delivery_type,
                "allowed_package_carrier_ids": [Command.set(other_carrier.ids)],
            }
        )

        wizard = self._make_wizard(picking)

        package_types = self.env["stock.package.type"].search(
            wizard.package_type_domain
        )
        self.assertIn(matching_type, package_types)
        self.assertNotIn(excluded_type, package_types)

    def test_domain_with_carrier_but_filter_disabled(self):
        picking = self._confirm_ship()
        picking.picking_type_id.filter_package_type_on_put_in_pack = False
        self.assertTrue(picking.carrier_id)
        wizard = self._make_wizard(picking)
        self.assertEqual([], wizard.package_type_domain)

    def test_domain_without_carrier_keeps_parent_domain(self):
        picking = self._confirm_ship()
        picking.carrier_id = False
        wizard = self._make_wizard(picking)
        self.assertEqual(
            [("package_carrier_type", "=", False)],
            wizard.package_type_domain,
        )
