# Copyright 2024 ACSONE SA/NV (https://www.acsone.eu)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo.addons.base.tests.common import BaseCommon

from .common import CommonChooseDeliveryPackage


class TestChooseDeliveryPackageType(CommonChooseDeliveryPackage, BaseCommon):
    def test_choose_delivery_package(self):
        """
        Check the domain is still the standard one.
        """
        sale = self._create_sale()
        sale.action_confirm()
        self.assertTrue(sale.picking_ids)
        res = sale.picking_ids.action_put_in_pack()
        model = res.get("res_model")
        context = res.get("context")
        self.assertEqual("choose.delivery.package", model)
        self.wizard = self.env[model].with_context(**context).create({})
        self.assertTrue(self.wizard)
        self.assertEqual(
            [("package_carrier_type", "=", "test")], self.wizard.package_type_domain
        )
