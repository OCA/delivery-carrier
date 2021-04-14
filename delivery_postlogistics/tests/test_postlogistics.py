# Copyright 2015-2019 Camptocamp
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from os.path import dirname, join

from odoo.tests import common

from vcr import VCR

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

ENDPOINT_URL = "https://wedecint.post.ch/"
CLIENT_ID = "XXX"
CLIENT_SECRET = "XXX"
LICENSE = "XXX"


class TestPostlogistics(common.SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.env["postlogistics.license"].create({"name": "TEST", "number": LICENSE})
        Product = cls.env["product.product"]
        partner_id = cls.env.ref("delivery_postlogistics.partner_postlogistics").id
        OptionTmpl = cls.env["postlogistics.delivery.carrier.template.option"]
        label_layout = OptionTmpl.create({"code": "A6", "partner_id": partner_id})
        output_format = OptionTmpl.create({"code": "PDF", "partner_id": partner_id})
        image_resolution = OptionTmpl.create({"code": "600", "partner_id": partner_id})

        cls.carrier = cls.env["delivery.carrier"].create(
            {
                "name": "Postlogistics",
                "delivery_type": "postlogistics",
                "product_id": Product.create({"name": "Shipping"}).id,
                "postlogistics_endpoint_url": ENDPOINT_URL,
                "postlogistics_client_id": CLIENT_ID,
                "postlogistics_client_secret": CLIENT_SECRET,
                "postlogistics_label_layout": label_layout.id,
                "postlogistics_output_format": output_format.id,
                "postlogistics_resolution": image_resolution.id,
            }
        )

        # Create Product packaging
        postlogistics_pd_packaging = cls.env["product.packaging"].create(
            {
                "name": "PRI-TEST",
                "package_carrier_type": "postlogistics",
                "shipper_package_code": "PRI, BLN",
            }
        )

        cls.env.user.company_id.write(
            {"street": "Rue de Lausanne 1", "zip": "1030", "city": "Bussigny"}
        )
        cls.env.user.company_id.partner_id.country_id = cls.env.ref("base.ch")
        cls.picking = cls.create_picking(cls, postlogistics_pd_packaging)
        cls.env.user.lang = "en_US"

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

    def create_picking(self, prod_packaging):
        Product = self.env["product.product"]
        stock_location = self.env.ref("stock.stock_location_stock")
        customer_location = self.env.ref("stock.stock_location_customers")
        Picking = self.env["stock.picking"]
        recipient = self.env["res.partner"].create(
            {
                "name": "Camptocamp SA",
                "street": "EPFL Innovation Park, Bât A",
                "zip": "1015",
                "city": "Lausanne",
            }
        )
        picking = Picking.create(
            {
                "partner_id": recipient.id,
                "carrier_id": self.carrier.id,
                "picking_type_id": self.env.ref("stock.picking_type_out").id,
                "location_id": stock_location.id,
                "location_dest_id": customer_location.id,
            }
        )
        product = Product.create({"name": "Product A"})

        self.env["stock.move"].create(
            {
                "name": "a move",
                "product_id": product.id,
                "product_uom_qty": 3.0,
                "product_uom": product.uom_id.id,
                "picking_id": picking.id,
                "location_id": stock_location.id,
                "location_dest_id": customer_location.id,
            }
        )

        # Add to the packages
        choose_delivery_package_wizard = self.env["choose.delivery.package"].create(
            {"picking_id": picking.id, "delivery_packaging_id": prod_packaging.id}
        )
        picking.action_assign()
        choose_delivery_package_wizard.put_in_pack()
        return picking
