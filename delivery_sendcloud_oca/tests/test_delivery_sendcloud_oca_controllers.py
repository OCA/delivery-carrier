# Copyright 2022 Onestein (<https://www.onestein.nl>)
# License OPL-1 (https://www.odoo.com/documentation/16.0/legal/licenses.html#odoo-apps).
import json
import logging
from os.path import dirname, join

import requests
from vcr import VCR

from odoo import http
from odoo.tests import Form, HttpCase, tagged
from odoo.tools import mute_logger

_super_send = requests.Session.send

logging.getLogger("vcr").setLevel(logging.WARNING)

recorder = VCR(
    record_mode="once",
    cassette_library_dir=join(dirname(__file__), "vcr_cassettes"),
    path_transformer=VCR.ensure_suffix(".yaml"),
    filter_headers=["Authorization"],
    decode_compressed_response=True,
)


@tagged("post_install", "-at_install")
class TestDeliverySendCloudControllers(HttpCase):
    @classmethod
    def _request_handler(cls, s, r, /, **kw):
        """Don't block external requests."""
        return _super_send(s, r, **kw)

    @mute_logger("py.warnings")
    def setUp(self):
        super().setUp()
        vals = {
            "shop_name": "API Integration " + self.env.company.name,
            "company_id": self.env.company.id,
            "public_key": "test",
            "secret_key": "test",
        }
        self.integration = self.env["sendcloud.integration"].create(vals)

    @mute_logger("py.warnings")
    def test_01_sendcloud_integration_credentials(self):
        self.integration.write({"public_key": False, "secret_key": False})
        res = self.url_open(
            url=f"/shop/sendcloud_integration_webhook/{self.env.company.id}",
            headers={
                "Content-Type": "application/json",
                "sendcloud-signature": "c841416e8b9aa99706bb08cbca1aec3b7c42"
                "edcad0318c7a311ea721054d3709",
            },
            data=json.dumps(
                {
                    "action": "integration_credentials",
                    "timestamp": 1719299439635,
                    "public_key": "test",
                    "secret_key": "test",
                    "integration_id": 241526,
                }
            ),
        )
        self.assertEqual(res.status_code, 200)

    @mute_logger("py.warnings")
    def test_02_sendcloud_integration_connected(self):
        self.integration.with_context(
            skip_update_in_sendcloud=True
        )._onchange_company_id()
        res = self.url_open(
            url=f"/shop/sendcloud_integration_webhook/{self.env.company.id}",
            headers={
                "Content-Type": "application/json",
                "sendcloud-signature": "7ffc4aa2e46bd49ad5e8b05eec3610eea"
                "32f4212e315c5b7957c997b8cd498b2",
            },
            data=json.dumps(
                {
                    "action": "integration_connected",
                    "timestamp": 1719299439635,
                    "integration": {
                        "id": 241526,
                        "shop_name": "API Integration My Company (San Francisco)",
                        "shop_url": False,
                        "system": "odoo",
                        "failing_since": None,
                        "last_fetch": None,
                        "service_point_enabled": False,
                        "service_point_carriers": [],
                        "webhook_active": False,
                        "webhook_url": False,
                        "import_weight": True,
                    },
                }
            ),
        )
        self.assertEqual(res.status_code, 200)

    @mute_logger("py.warnings")
    def test_03_sendcloud_integration_updated(self):
        self.integration.with_context(
            skip_update_in_sendcloud=True
        )._inverse_service_point_carrier_ids()
        res = self.url_open(
            url=f"/shop/sendcloud_integration_webhook/{self.env.company.id}",
            headers={
                "Content-Type": "application/json",
                "sendcloud-signature": "5e63fa9743314892524ee1c54c1f2"
                "e3b9b2868d98bcde37b8c54c4e9bfc54d37",
            },
            data=json.dumps(
                {
                    "action": "integration_updated",
                    "timestamp": 1719299439635,
                    "integration": {
                        "id": 241526,
                        "shop_name": "API Integration My Company (San Francisco)",
                        "shop_url": False,
                        "system": "odoo",
                        "failing_since": None,
                        "last_fetch": None,
                        "service_point_enabled": False,
                        "service_point_carriers": [],
                        "webhook_active": False,
                        "webhook_url": False,
                        "import_weight": True,
                    },
                }
            ),
        )
        self.assertEqual(res.status_code, 200)

    @mute_logger("py.warnings")
    def test_04_sendcloud_integration_deleted(self):
        res = self.url_open(
            url=f"/shop/sendcloud_integration_webhook/{self.env.company.id}",
            headers={
                "Content-Type": "application/json",
                "sendcloud-signature": "65b41fd7bded98284367b102f8c869"
                "e59a934cee9fb26a54fde715b212f7f47f",
            },
            data=json.dumps(
                {
                    "action": "integration_deleted",
                    "timestamp": 1719299439635,
                    "integration": {
                        "id": 241526,
                        "shop_name": "API Integration My Company (San Francisco)",
                        "shop_url": False,
                        "system": "odoo",
                        "failing_since": None,
                        "last_fetch": None,
                        "service_point_enabled": False,
                        "service_point_carriers": [],
                        "webhook_active": False,
                        "webhook_url": False,
                        "import_weight": True,
                    },
                }
            ),
        )
        self.assertEqual(res.status_code, 200)

    @mute_logger("py.warnings")
    def test_05_sendcloud_parcel_status_changed(self):
        res = self.url_open(
            url=f"/shop/sendcloud_integration_webhook/{self.env.company.id}",
            headers={
                "Content-Type": "application/json",
                "sendcloud-signature": "0750d0fb91425fc9a193194f5f97bedf"
                "2993bcd7213cb85f9d6f6fecdf3e6cb9",
            },
            data=json.dumps(
                {
                    "action": "parcel_status_changed",
                    "timestamp": 1719299439635,
                    "parcel": {
                        "id": 3,
                        "external_order_id": "58e6e33e-a952-4b8e-afdd-4cddeaf4f665",
                        "external_shipment_id": "bfdebf74-853d-4c32-9484-e0201426f888",
                        "shipment_uuid": "ac37f648-18af-4a37-92ee-0fce58998d2c",
                        "name": "Deco Addict",
                        "company_name": "Deco Addict",
                        "address": "77 Santa Barbara Rd",
                        "city": "Pleasant Hill",
                        "postal_code": "94523",
                        "telephone": "(603)-996-3829",
                        "email": "deco_addict@yourcompany.example.com",
                        "date_created": "01-01-2018 21:45:30",
                        "date_updated": "01-01-2018 21:47:12",
                        "date_announced": "01-01-2018 21:47:13",
                        "weight": "0.1",
                        "status": {"id": 0, "message": "Ready to send"},
                        "data": {},
                        "country": {
                            "iso_3": "USA",
                            "iso_2": "US",
                            "name": "United States",
                        },
                        "shipment": {
                            "id": 8,
                            "name": "DHL Express Worldwide 0-1kg - incoterm DAP",
                        },
                        "carrier": {"code": "dhl"},
                        "is_return": False,
                        "total_order_value_currency": "USD",
                        "total_order_value": "505",
                        "colli_uuid": "88296eff-595c-4c62-9b6f-075112bf54f6",
                        "collo_nr": 0,
                        "collo_count": 1,
                        "awb_tracking_number": False,
                        "box_number": False,
                        "length": False,
                        "width": False,
                        "height": False,
                        "shipping_method_checkout_name": "DHL Express Worldwide"
                        " 0-1kg - incoterm DAP",
                        "external_reference": "WH/OUT/00524,0",
                    },
                }
            ),
        )
        self.assertEqual(res.status_code, 200)

    @mute_logger("py.warnings")
    def test_06_sendcloud_picking_download_labels(self):
        self.integration.sendcloud_code = 241526
        delivery_carrier_obj = self.env["delivery.carrier"]
        # Retrieve Sendcloud shipping methods
        with recorder.use_cassette("shipping_methods"):
            delivery_carrier_obj.sendcloud_sync_shipping_method()
        shipping_method0 = delivery_carrier_obj.search(
            [("delivery_type", "=", "sendcloud")], limit=1
        )
        sale_order = self.env.ref("sale.sale_order_1").copy()
        # Set Sendcloud delivery method
        choose_delivery_form = Form(
            self.env["choose.delivery.carrier"].with_context(
                **{
                    "default_order_id": sale_order.id,
                    "default_carrier_id": shipping_method0.id,
                }
            )
        )
        choose_delivery_wizard = choose_delivery_form.save()
        choose_delivery_wizard.button_confirm()
        is_product_harmonized_system_installed = self.env["ir.module.module"].search(
            [("name", "=", "product_harmonized_system"), ("state", "=", "installed")],
            limit=1,
        )
        if is_product_harmonized_system_installed:
            sale_order.mapped("order_line.product_id").write(
                {
                    "hs_code_id": self.env.ref("product_harmonized_system.84715000").id,
                    "origin_country_id": sale_order.warehouse_id.partner_id.country_id,
                }
            )
        else:
            sale_order.mapped("order_line.product_id").write(
                {
                    "hs_code": "123",
                    "country_of_origin": sale_order.warehouse_id.partner_id.country_id,
                }
            )
        with recorder.use_cassette("shipping_02"):
            sale_order.with_context(
                force_sendcloud_shipment_code="c9b2058d-2621-4ce5-afb0-f14e8e5565b6"
            ).action_confirm()
        self.authenticate("admin", "admin")
        res = self.url_open(
            url="/sendcloud/picking/download_labels",
            data={
                "ids": sale_order.picking_ids.ids,
                "csrf_token": http.Request.csrf_token(self),
            },
        )
        self.assertEqual(res.status_code, 200)
