# Copyright 2021 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
from contextlib import contextmanager
from os.path import dirname, join

import requests
from requests import PreparedRequest, Session
from vcr import VCR
from vcr.record_mode import RecordMode

from odoo import api
from odoo.modules.registry import Registry
from odoo.tools.safe_eval import json

from odoo.addons.base.tests.common import BaseCommon

from ..postlogistics.web_service import GENERATE_LABEL_PATH, PostlogisticsWebService

ENDPOINT_URL = "https://wedecint.post.ch/"
CLIENT_ID = "XXX"
CLIENT_SECRET = "XXX"
LICENSE = "XXX"


recorder = VCR(
    record_mode=RecordMode.ONCE,
    cassette_library_dir=join(dirname(__file__), "fixtures/cassettes"),
    path_transformer=VCR.ensure_suffix(".yaml"),
    filter_headers=["Authorization"],
    filter_post_data_parameters=["client_id", "client_secret"],
    # ignore scheme, host, port
    match_on=("method", "path", "query"),
    # allow to read and edit content in cassettes
    decode_compressed_response=True,
)


def check_generate_label_body(request, saved_request):
    """
    Check if the body of the generate label request is the same as the saved
    one
    """
    assert request.path == saved_request.path

    if request.path == GENERATE_LABEL_PATH:
        query_json = json.loads(request.body.decode("utf-8"))
        saved_json = json.loads(saved_request.body.decode("utf-8"))
        query_json["item"]["itemID"] = saved_json["item"]["itemID"]
        assert (
            query_json == saved_json
        ), "Body request not corresponding to the saved one"


recorder.register_matcher("generate_label_body", check_generate_label_body)


_super_send = requests.Session.send


class TestPostlogisticsCommon(BaseCommon):
    @classmethod
    def _request_handler(cls, s: Session, r: PreparedRequest, /, **kw):
        # We need to override Odoo check to allow API testing
        if r.url.startswith(ENDPOINT_URL):
            return _super_send(s, r, **kw)
        return super()._request_handler(s, r, **kw)

    @classmethod
    def setUpClassWebservice(cls):
        cls.service_class = PostlogisticsWebService(cls.env.user.company_id)

    @classmethod
    def setUpClassUserCompany(cls):
        cls.env.user.company_id.write(
            {"street": "Rue de Lausanne 1", "zip": "1030", "city": "Bussigny"}
        )
        cls.env.user.company_id.partner_id.country_id = cls.env.ref("base.ch")
        cls.env.user.lang = "en_US"

    @classmethod
    def setUpClassLocation(cls):
        cls.stock_location = cls.env.ref("stock.stock_location_stock")
        cls.customer_location = cls.env.ref("stock.stock_location_customers")

    @classmethod
    def setUpClassLicense(cls):
        cls.license = cls.env["postlogistics.license"].create(
            {"name": "TEST", "number": LICENSE}
        )

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.setUpClassWebservice()
        cls.setUpClassUserCompany()
        cls.setUpClassLocation()
        cls.setUpClassLicense()

    def setUpCarrier(self):
        shipping_product = self.env["product.product"].create({"name": "Shipping"})
        option_model = self.env["delivery.carrier.template.option"]
        partner_id = self.env.ref("delivery_postlogistics.partner_postlogistics").id
        label_layout = option_model.create({"code": "A6", "partner_id": partner_id})
        output_format = option_model.create({"code": "PDF", "partner_id": partner_id})
        image_resolution = option_model.create(
            {"code": "600", "partner_id": partner_id}
        )
        self.carrier = self.env["delivery.carrier"].create(
            {
                "name": "Postlogistics",
                "delivery_type": "postlogistics",
                "product_id": shipping_product.id,
                "postlogistics_endpoint_url": ENDPOINT_URL,
                "postlogistics_client_id": CLIENT_ID,
                "postlogistics_client_secret": CLIENT_SECRET,
                "postlogistics_license_id": self.license.id,
                "postlogistics_label_layout": label_layout.id,
                "postlogistics_output_format": output_format.id,
                "postlogistics_resolution": image_resolution.id,
            }
        )

    def setUpPackaging(self):
        self.postlogistics_default_package_type = self.env.ref(
            "delivery_postlogistics.postlogistics_default_package_type"
        )

    def setUp(cls):
        super().setUp()
        cls.setUpCarrier()
        cls.setUpPackaging()

    @contextmanager
    def open_new_env(self):
        with Registry(self.env.cr.dbname).cursor() as new_cr:
            yield api.Environment(new_cr, self.env.uid, self.env.context)

    def create_picking(self, partner=None, product_matrix=None):
        package_type = self.postlogistics_default_package_type
        if not partner:
            partner = self.env["res.partner"].create(
                {
                    "name": "Camptocamp SA",
                    "street": "EPFL Innovation Park, Bât A",
                    "zip": "1015",
                    "city": "Lausanne",
                }
            )
        picking = self.env["stock.picking"].create(
            {
                "partner_id": partner.id,
                "carrier_id": self.carrier.id,
                "picking_type_id": self.env.ref("stock.picking_type_out").id,
                "location_id": self.stock_location.id,
                "location_dest_id": self.customer_location.id,
            }
        )
        if not product_matrix:
            product_matrix = [
                (self.env["product.product"].create({"name": "Product A"}), 3),
            ]
        for product, qty in product_matrix:
            self.env["stock.move"].create(
                {
                    "name": product.name,
                    "product_id": product.id,
                    "product_uom_qty": qty,
                    "product_uom": product.uom_id.id,
                    "picking_id": picking.id,
                    "location_id": self.stock_location.id,
                    "location_dest_id": self.customer_location.id,
                }
            )
        choose_delivery_package_wizard = self.env["choose.delivery.package"].create(
            {"picking_id": picking.id, "delivery_package_type_id": package_type.id}
        )
        picking.action_assign()
        choose_delivery_package_wizard.action_put_in_pack()
        return picking
