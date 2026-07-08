# Copyright 2026 Camptocamp SA (https://www.camptocamp.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo import Command

from odoo.addons.base.tests.common import BaseCommon
from odoo.addons.stock_picking_delivery_package_type_domain.tests.common import (
    CommonChooseDeliveryPackage,
)


class TestChooseDeliveryPackageType(CommonChooseDeliveryPackage, BaseCommon):
    def _get_choose_delivery_package_wizard(self, picking):
        action = picking.action_put_in_pack()
        wizard_model = action.get("res_model")
        wizard_context = action.get("context")
        return self.env[wizard_model].with_context(**wizard_context).create({})

    def test_domain_gets_correct_package_type(self):
        sale = self._create_sale()
        sale.action_confirm()
        self.assertTrue(sale.picking_ids)
        carrier = sale.picking_ids.carrier_id
        wizard = self._get_choose_delivery_package_wizard(sale.picking_ids)
        self.assertEqual("choose.delivery.package", wizard._name)
        self.wizard = wizard
        self.assertTrue(self.wizard)
        self.assertEqual(
            self.wizard.package_type_domain,
            [
                "&",
                ("package_carrier_type", "=", carrier.delivery_type),
                "|",
                ("allowed_package_carrier_ids", "=", False),
                ("allowed_package_carrier_ids", "in", carrier.ids),
            ],
        )

    def test_domain_excludes_package_types_of_other_carriers(self):
        sale = self._create_sale()
        sale.action_confirm()
        self.assertTrue(sale.picking_ids)

        picking = sale.picking_ids
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

        wizard = self._get_choose_delivery_package_wizard(picking)

        package_types = self.env["stock.package.type"].search(
            wizard.package_type_domain
        )
        self.assertIn(matching_type, package_types)
        self.assertNotIn(excluded_type, package_types)

    def test_domain_without_carrier_keeps_parent_domain(self):
        sale = self._create_sale()
        sale.action_confirm()
        self.assertTrue(sale.picking_ids)

        picking = sale.picking_ids
        picking.carrier_id = False

        wizard = (
            self.env["choose.delivery.package"]
            .with_context(
                default_picking_id=picking.id,
                current_package_carrier_type="none",
            )
            .create({})
        )

        self.assertEqual(
            [("package_carrier_type", "=", "none")],
            wizard.package_type_domain,
        )
