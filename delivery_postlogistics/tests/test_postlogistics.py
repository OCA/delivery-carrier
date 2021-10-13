# Copyright 2015-2019 Camptocamp
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from os.path import dirname, join

from vcr import VCR

from odoo import exceptions

from .common import TestPostlogisticsCommon

recorder = VCR(
    record_mode="once",
    cassette_library_dir=join(dirname(__file__), "fixtures/cassettes"),
    path_transformer=VCR.ensure_suffix(".yaml"),
    filter_headers=["Authorization", "Date"],
    filter_post_data_parameters=[
        ("client_id", "XXX"),
        ("client_secret", "XXX"),
        ("frankingLicense", "XXX"),
    ],
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

    @recorder.use_cassette
    def test_1_store_label(self):
        res = self.picking._generate_postlogistics_label(skip_attach_file=True)
        ref = "996001321700016917"
        self.assertEqual(res[0]["file_type"], "pdf")
        self.assertEqual(res[0]["name"], "{}.pdf".format(ref))
        self.assertEqual(res[0]["file"][:30], b"JVBERi0xLjQKJeLjz9MKMiAwIG9iag")
        self.assertEqual(self.picking.carrier_tracking_ref, ref)

    @recorder.use_cassette
    def test_2_missing_language(self):
        self.env.user.lang = False
        self.picking._generate_postlogistics_label(skip_attach_file=True)

    def test_3_cod_amount(self):
        """Since there's no SO attached to the picking we shouldn't be
        able to retrieve the cash on delivery.
        An error should be raised if BLN is in the shipper package code.
        """
        self.postlogistics_pd_packaging.shipper_package_code = "PRI, BLN"
        regex = (
            "The cash on delivery is only available " "if there's a related sale order."
        )
        with self.assertRaisesRegex(exceptions.Warning, regex):
            self.picking._generate_postlogistics_label(skip_attach_file=True)
