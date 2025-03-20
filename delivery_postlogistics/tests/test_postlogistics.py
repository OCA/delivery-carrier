# Copyright 2015 Camptocamp
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo.exceptions import UserError

from .common import TestPostlogisticsCommon, recorder

LABEL_BASE64 = b"R0lGODlhAQABAIAAAP///wAAACwAAAAAAQABAAACAkQBADs=="


class TestPostlogistics(TestPostlogisticsCommon):
    def setUp(self):
        super().setUp()
        self.picking = self.create_picking()

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
        customer = self.picking.postlogistics_label_prepare_recipient()
        self.assertEqual(customer["country"], "FR")
        self.assertEqual(customer["name2"], "Camptocamp SA")

    def test_store_label(self):
        with recorder.use_cassette(
            "test_store_label", allow_playback_repeats=True
        ) as cassette:
            labels = self.picking.generate_postlogistics_shipping_labels()
            self.assertEqual(len(cassette.requests), 2)
            ref = "996001321700005959"
            self.assertEqual(labels[0]["file_type"], "pdf")
            self.assertEqual(labels[0]["name"], f"{ref}.pdf")
            self.assertEqual(labels[0]["file"], LABEL_BASE64)
            self.assertEqual(self.picking.carrier_tracking_ref, ref)

    def test_missing_language(self):
        self.env.user.lang = False
        with recorder.use_cassette(
            "test_missing_language", allow_playback_repeats=True
        ) as cassette:
            self.picking.generate_postlogistics_shipping_labels()
            self.assertEqual(len(cassette.requests), 2)

    def test_store_label_postlogistics_tracking_format_picking_num(self):
        self.picking.carrier_id.postlogistics_tracking_format = "picking_num"
        with recorder.use_cassette(
            "test_store_label", allow_playback_repeats=True
        ) as cassette:
            labels = self.picking.generate_postlogistics_shipping_labels()
            self.assertEqual(len(cassette.requests), 2)
            ref = "996001321700005959"
            self.assertEqual(labels[0]["file_type"], "pdf")
            self.assertEqual(labels[0]["name"], f"{ref}.pdf")
            self.assertEqual(labels[0]["file"], LABEL_BASE64)
            self.assertEqual(self.picking.carrier_tracking_ref, ref)

    def test_send_to_shipper(self):
        with recorder.use_cassette(
            "test_store_label", allow_playback_repeats=True
        ) as cassette:
            self.picking.send_to_shipper()
            self.assertEqual(len(cassette.requests), 2)

    def test_send_to_shipper_default_package(self):
        pl_package_type = self.postlogistics_default_package_type
        self.carrier.postlogistics_default_package_type_id = pl_package_type
        self.picking.move_line_ids.write(
            {
                "result_package_id": False,
            }
        )
        with recorder.use_cassette(
            "test_store_label", allow_playback_repeats=True
        ) as cassette:
            self.picking.send_to_shipper()
            self.assertEqual(len(cassette.requests), 2)

    def test_postlogistics_rate_shipment(self):
        with recorder.use_cassette(
            "test_store_label", allow_playback_repeats=True
        ) as cassette:
            res = self.carrier.postlogistics_rate_shipment(None)
            self.assertEqual(len(cassette.requests), 2)
            self.assertEqual(res["price"], 1.0)

    def test_postlogistics_get_token_error(self):
        with recorder.use_cassette(
            "test_token_error", allow_playback_repeats=True
        ) as cassette:
            err_msg = (
                "Postlogistics service is not accessible at the moment. Error code:"
                " 503. "
                "Please try again later."
            )
            with self.assertRaisesRegex(UserError, err_msg):
                self.service_class._request_access_token(self.carrier)
                self.assertEqual(len(cassette.requests), 1)
