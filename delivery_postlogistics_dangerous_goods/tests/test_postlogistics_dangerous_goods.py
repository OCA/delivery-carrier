# Copyright 2021 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo.addons.delivery_postlogistics.tests.common import TestPostlogisticsCommon

from ..postlogistics.web_service import PostlogisticsWebServiceDangerousGoods


class TestPostlogisticsDangerousGoods(TestPostlogisticsCommon):
    @classmethod
    def setUpClassProduct(cls):
        limited_amount_lq = cls.env.ref(
            "l10n_eu_product_adr_dangerous_goods.limited_amount_1"
        )
        weapon_good = cls.env.ref("l10n_eu_product_adr.adr_goods_0007")
        # Create products
        cls.dangerous_weapon = cls.env["product.product"].create(
            {
                "name": "Knife-Wrench",
                "limited_amount_id": limited_amount_lq.id,
                "adr_goods_id": weapon_good.id,
                "is_dangerous": True,
            }
        )
        cls.product_no_lq = cls.env["product.product"].create({"name": "Wrench"})

    @classmethod
    def setUpClassWebservice(cls):
        super().setUpClassWebservice()
        cls.service_class = PostlogisticsWebServiceDangerousGoods(
            cls.env.user.company_id
        )

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.setUpClassProduct()

    def test_json_no_dangerous_goods(self):
        # When there's no dangerous goods in the package,
        # no unnumber should be sent through the api
        products = [(self.product_no_lq, 10.0)]
        picking = self.create_picking(product_matrix=products)
        package_ids = picking._get_packages_from_picking()
        recipient = self.service_class._prepare_recipient(picking)
        item_list = self.service_class._prepare_item_list(
            picking, recipient, package_ids
        )
        attributes = item_list[0]["attributes"]
        self.assertFalse(attributes.get("unnumbers"))
        self.assertNotIn("LQ", attributes["przl"])

    def test_json_dangerous_goods(self):
        # When there's dangerous goods in the package,
        # we should have the list of unnumbers
        products = [(self.dangerous_weapon, 10.0)]
        picking = self.create_picking(product_matrix=products)
        package_ids = picking._get_packages_from_picking()
        recipient = self.service_class._prepare_recipient(picking)
        item_list = self.service_class._prepare_item_list(
            picking, recipient, package_ids
        )
        expected_unnumbers = [
            7,
        ]
        attributes = item_list[0]["attributes"]
        self.assertEqual(attributes["unnumbers"], expected_unnumbers)
        self.assertIn("LQ", attributes["przl"])
