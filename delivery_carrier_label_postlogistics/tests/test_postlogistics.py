# Copyright 2015-2019 Camptocamp
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from os.path import dirname, join

from vcr import VCR

from odoo.tests import common


recorder = VCR(
    record_mode='once',
    cassette_library_dir=join(dirname(__file__), 'fixtures/cassettes'),
    path_transformer=VCR.ensure_suffix('.yaml'),
    filter_headers=['Authorization'],
    filter_post_data_parameters=['client_id', 'client_secret'],
    # ignore scheme, host, port
    match_on=('method', 'path', 'query'),
    # allow to read and edit content in cassettes
    decode_compressed_response=True,
)

AUTH_URL = "https://wedecint.post.ch/WEDECOAuth/token"
GENERATE_LABEL_URL = "https://wedecint.post.ch/api/barcode/v1/generateAddressLabel"
CLIENT_ID = "XXX"
CLIENT_SECRET = "XXX"
LICENSE = "XXX"


class TestPostlogistics(common.SavepointCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        ICP = cls.env["ir.config_parameter"]
        ICP.set_param("postlogistics.oauth.client_id", CLIENT_ID)
        ICP.set_param("postlogistics.oauth.client_secret", CLIENT_SECRET)
        ICP.set_param("postlogistics.oauth.authentication_url", AUTH_URL)
        ICP.set_param(
            "postlogistics.oauth.generate_label_url", GENERATE_LABEL_URL
        )
        cls.env["postlogistics.license"].create(
            {
                'name': 'TEST',
                'number': LICENSE,
            }
        )
        Product = cls.env['product.product']
        partner_id = cls.env.ref(
            'delivery_carrier_label_postlogistics.partner_postlogistics').id
        cls.carrier = cls.env['delivery.carrier'].create({
            'name': 'Postlogistics',
            'delivery_type': 'postlogistics',
            'product_id': Product.create({'name': 'Shipping'}).id,
        })
        OptionTmpl = cls.env['delivery.carrier.template.option']

        service_opt_tmpl = OptionTmpl.create(
            {"code": "PRI"}
        )
        label_layout = OptionTmpl.create(
            {'code': 'A6', 'partner_id': partner_id})
        output_format = OptionTmpl.create(
            {'code': 'PDF', 'partner_id': partner_id})
        image_resolution = OptionTmpl.create(
            {'code': '600', 'partner_id': partner_id})

        Option = cls.env['delivery.carrier.option']
        service_opt = Option.create(
            {"code": "PRI", "partner_id": partner_id,
             "postlogistics_type": "basic",
             "tmpl_option_id": service_opt_tmpl.id,
             }
        )

        cls.env.user.company_id.write({
            'postlogistics_label_layout': label_layout.id,
            'postlogistics_output_format': output_format.id,
            'postlogistics_resolution': image_resolution.id,
            "street": "Rue de Lausanne 1",
            "zip": "1030",
            "city": "Bussigny",
        })
        cls.env.user.company_id.partner_id.country_id = cls.env.ref("base.ch")
        stock_location = cls.env.ref('stock.stock_location_stock')
        customer_location = cls.env.ref('stock.stock_location_customers')
        Picking = cls.env['stock.picking']
        recipient = cls.env["res.partner"].create(
            {
                "name": "Camptocamp SA",
                "street": "EPFL Innovation Park, Bât A",
                "zip": "1015",
                "city": "Lausanne",
            }
        )
        cls.picking = Picking.create({
            'partner_id': recipient.id,
            'carrier_id': cls.carrier.id,
            'picking_type_id': cls.env.ref('stock.picking_type_out').id,
            'location_id': stock_location.id,
            'location_dest_id': customer_location.id,
            'option_ids': [(4, service_opt.id, 0)],
        })
        product = Product.create({'name': 'Product A'})

        cls.env['stock.move'].create({
            'name': 'a move',
            'product_id': product.id,
            'product_uom_qty': 3.0,
            'product_uom': product.uom_id.id,
            'picking_id': cls.picking.id,
            'location_id': stock_location.id,
            'location_dest_id': customer_location.id,
        })
        cls.env.user.lang = 'en_US'
        # creating the default package requires to have move lines
        # thus the picking must be confirmed
        cls.picking.action_assign()
        cls.picking.action_confirm()
        cls.picking._set_a_default_package()

    def test_store_label(self):
        with recorder.use_cassette('test_store_label') as cassette:
            res = self.picking._generate_postlogistics_label()
            self.assertEqual(len(cassette.requests), 2)
        ref = "996001321700005959"
        self.assertEqual(res[0]["file_type"], "pdf")
        self.assertEqual(res[0]["name"], "{}.pdf".format(ref))
        self.assertEqual(res[0]["file"][:30], b"JVBERi0xLjQKJeLjz9MKMiAwIG9iag")
        self.assertEqual(res[0]["tracking_number"], ref)

    def test_missing_language(self):
        self.env.user.lang = False
        with recorder.use_cassette('test_missing_language') as cassette:
            res = self.picking._generate_postlogistics_label()
            self.assertEqual(len(cassette.requests), 2)
        ref = "996001321700005958"
        self.assertEqual(res[0]["file_type"], "pdf")
        self.assertEqual(res[0]["name"], "{}.pdf".format(ref))
        self.assertEqual(res[0]["file"][:30], b"JVBERi0xLjQKJeLjz9MKMiAwIG9iag")
        self.assertEqual(res[0]["tracking_number"], ref)
