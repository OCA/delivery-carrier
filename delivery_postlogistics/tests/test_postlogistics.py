# Copyright 2015-2019 Camptocamp
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from os.path import dirname, join

from vcr import VCR

from .common import TestPostlogisticsCommon

recorder = VCR(
    record_mode="once",
    cassette_library_dir=join(dirname(__file__), "fixtures/cassettes"),
    path_transformer=VCR.ensure_suffix(".yaml"),
    filter_headers=["Authorization"],
    filter_post_data_parameters=["client_id", "client_secret"],
    # ignore scheme, host, port
    match_on=("method", "path", "query"),
    # allow to read and edit content in cassettes
    decode_compressed_response=True,
)


class TestPostlogistics(TestPostlogisticsCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.picking = cls.create_picking()

    def test_misc(self):
        self.assertFalse(self.carrier.prod_environment)
        self.carrier.toggle_prod_environment()
        self.carrier.onchange_prod_environment()
        self.assertTrue(self.carrier.prod_environment)
        self.carrier.toggle_prod_environment()
        self.carrier.onchange_prod_environment()
        self.assertFalse(self.carrier.prod_environment)
        self.assertEqual(
            self.carrier.get_tracking_link(self.picking),
            "https://service.post.ch/EasyTrack/"
            "submitParcelData.do?formattedParcelCodes=False",
        )

    def test_store_label(self):
        with recorder.use_cassette("test_store_label") as cassette:
            res = self.picking._generate_postlogistics_label(skip_attach_file=True)
            self.assertEqual(len(cassette.requests), 2)
        ref = "996001321700005959"
        self.assertEqual(res[0]["file_type"], "pdf")
        self.assertEqual(res[0]["name"], "{}.pdf".format(ref))
        self.assertEqual(res[0]["file"][:30], b"JVBERi0xLjQKJeLjz9MKMiAwIG9iag")
        self.assertEqual(self.picking.carrier_tracking_ref, ref)

    def test_missing_language(self):
        self.env.user.lang = False
        with recorder.use_cassette("test_missing_language") as cassette:
            self.picking._generate_postlogistics_label(skip_attach_file=True)
            self.assertEqual(len(cassette.requests), 2)

    def test_store_label_postlogistics_tracking_format_picking_num(self):
        self.carrier.postlogistics_tracking_format = "picking_num"
        with recorder.use_cassette("test_store_label") as cassette:
            res = self.picking._generate_postlogistics_label(skip_attach_file=True)
            self.assertEqual(len(cassette.requests), 2)
        ref = "996001321700005959"
        self.assertEqual(res[0]["file_type"], "pdf")
        self.assertEqual(res[0]["name"], "{}.pdf".format(ref))
        self.assertEqual(res[0]["file"][:30], b"JVBERi0xLjQKJeLjz9MKMiAwIG9iag")
        self.assertEqual(self.picking.carrier_tracking_ref, ref)

    def test_prepare_recipient(self):
        partner_id = self.picking.partner_id
        partner_id.is_company = True
        partner_id.country_id = self.env.ref("base.fr").id
        recipient = self.env["res.partner"].create(
            {
                "name": "Recipient",
                "street": "EPFL Innovation Park, Bât A",
                "zip": "1015",
                "city": "Lausanne",
                "street2": "Street 2",
                "parent_id": partner_id.id,
                "company_name": "Camptocamp",
            }
        )
        self.picking.partner_id = recipient
        customer = self.service_class._prepare_recipient(self.picking)
        self.assertEqual(customer["country"], "FR")
        self.assertEqual(customer["name2"], "Camptocamp SA")

    def test_send_to_shipper(self):
        with recorder.use_cassette("test_store_label") as cassette:
            self.picking.send_to_shipper()
            self.assertEqual(len(cassette.requests), 2)

    def test_send_to_shipper_default_package(self):
        pl_package_type = self.postlogistics_pd_package_type
        self.carrier.postlogistics_default_package_type_id = pl_package_type
        self.picking.move_line_ids.write(
            {
                "result_package_id": False,
            }
        )
        with recorder.use_cassette("test_store_label") as cassette:
            self.picking.send_to_shipper()
            self.assertEqual(len(cassette.requests), 2)

    def test_postlogistics_rate_shipment(self):
        with recorder.use_cassette("test_store_label") as cassette:
            res = self.carrier.postlogistics_rate_shipment(None)
            self.assertEqual(len(cassette.requests), 2)
        self.assertEqual(res["price"], 1.0)
