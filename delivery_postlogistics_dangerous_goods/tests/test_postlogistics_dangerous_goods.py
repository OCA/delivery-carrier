# Copyright 2021 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from os.path import dirname, join

from odoo import exceptions

from odoo.addons.delivery_postlogistics.tests.common import TestPostlogisticsCommon

from vcr import VCR

from ..postlogistics.web_service import PostlogisticsWebServiceDangerousGoods

recorder = VCR(
    record_mode="once",
    cassette_library_dir=join(dirname(__file__), "fixtures/cassettes"),
    path_transformer=VCR.ensure_suffix(".yaml"),
    filter_headers=["Authorization"],
    # ignore scheme, host, port
    match_on=("method", "path", "query"),
    # allow to read and edit content in cassettes
    decode_compressed_response=True,
)


class TestPostlogisticsDangerousGoods(TestPostlogisticsCommon):
    @classmethod
    def setUpClassProduct(cls):
        # Create UNNumbers
        un_reference_model = cls.env["un.reference"]
        unnumber_valid = un_reference_model.create(
            {"name": "1234", "description": "Valid UNNumber"}
        )
        unnumber_non_valid = un_reference_model.create(
            {"name": "1234,", "description": "Non-valid UNNumber"}
        )

        limited_amount_lq = cls.env.ref("l10n_eu_product_adr.limited_amount_1")

        # Create products
        cls.product_lq = cls.env["product.product"].create(
            {
                "name": "Product LQ",
                "un_ref": unnumber_valid.id,
                "limited_amount_id": limited_amount_lq.id,
                "is_dangerous": True,
                "is_dangerous_good": True,
            }
        )
        cls.product_lq_wrong_number = cls.env["product.product"].create(
            {
                "name": "Product LQ wrong UNNumber",
                "un_ref": unnumber_non_valid.id,
                "limited_amount_id": limited_amount_lq.id,
                "is_dangerous": True,
                "is_dangerous_good": True,
            }
        )
        cls.product_no_lq = cls.env["product.product"].create({"name": "Product no LQ"})

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

    @recorder.use_cassette
    def test_validate_wrong_unnumber(self):
        # Should raise an exception if unnumber is not a 4 digits long string
        products = [(self.product_lq_wrong_number, 10.0)]
        picking = self.create_picking(product_matrix=products)
        with self.assertRaises(exceptions.UserError):
            picking._generate_postlogistics_label()

    @recorder.use_cassette
    def test_confirm_right_unnumber(self):
        products = [(self.product_lq, 10.0)]
        picking = self.create_picking(product_matrix=products)
        picking._generate_postlogistics_label()

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
        self.assertFalse(item_list[0]["attributes"].get("unnumbers"))

    def test_json_dangerous_goods(self):
        # When there's dangerous goods in the package,
        # we should have the list of unnumbers
        products = [(self.product_lq, 10.0)]
        picking = self.create_picking(product_matrix=products)
        package_ids = picking._get_packages_from_picking()
        recipient = self.service_class._prepare_recipient(picking)
        item_list = self.service_class._prepare_item_list(
            picking, recipient, package_ids
        )
        expected_unnumbers = [
            1234,
        ]
        self.assertEqual(item_list[0]["attributes"]["unnumbers"], expected_unnumbers)
