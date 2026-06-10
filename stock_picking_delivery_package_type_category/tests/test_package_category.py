from odoo.addons.base.tests.common import BaseCommon
from odoo.addons.stock_picking_delivery_package_type_domain.tests.common import (
    CommonChooseDeliveryPackage,
)


class TestChooseDeliveryPackageType(CommonChooseDeliveryPackage, BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.fridge = cls.env["stock.package.type.category"].create(
            {
                "name": "Fridge",
                "code": "FRIDGE",
            }
        )
        cls.medium_box = cls.env["stock.package.type"].create(
            {
                "name": "Medium Box Fridge",
                "category_id": cls.fridge.id,
            }
        )
        cls.env.ref(
            "stock.picking_type_out"
        ).authorized_package_type_cateogory_ids = cls.fridge

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
        self.assertIn(
            ("category_id", "in", self.fridge.ids), self.wizard.package_type_domain
        )
