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
