# Copyright 2022 Onestein (<https://www.onestein.nl>)
# License OPL-1 (https://www.odoo.com/documentation/16.0/legal/licenses.html#odoo-apps).

import base64
import json
import logging
from contextlib import contextmanager
from os.path import dirname, join
from unittest.mock import patch

import requests
import responses
from vcr import VCR

from odoo.exceptions import UserError, ValidationError
from odoo.tests import Form
from odoo.tools import mute_logger

from odoo.addons.base.tests.common import BaseCommon

from .common import MINIMAL_PDF, SendcloudSaleOrderMixin

_super_send = requests.Session.send

logging.getLogger("vcr").setLevel(logging.WARNING)

recorder = VCR(
    record_mode="once",
    cassette_library_dir=join(dirname(__file__), "vcr_cassettes"),
    path_transformer=VCR.ensure_suffix(".yaml"),
    filter_headers=["Authorization"],
    decode_compressed_response=True,
)


class TestDeliverySendCloud(SendcloudSaleOrderMixin, BaseCommon):
    @classmethod
    def _request_handler(cls, s, r, /, **kw):
        """Don't block external requests."""
        return _super_send(s, r, **kw)

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Every Sendcloud API call is logged through a cursor of its own, so
        # the registry has to hand out test cursors for those writes to be
        # rolled back along with the test.
        cls.registry_enter_test_mode_cls()

    @mute_logger("py.warnings")
    def setUp(self):
        super().setUp()
        form = Form(self.env["sendcloud.integration.wizard"])
        wizard = form.save()
        wizard.base_url = "https://f482-185-247-144-87.eu.ngrok.io"
        with recorder.use_cassette("get_integration"):
            wizard.button_update()
        self.integration = self.env["sendcloud.integration"].search([])
        self.assertEqual(len(self.integration), 1)
        self.integration.public_key = "test"
        self.integration.secret_key = "test"
        self.integration.sendcloud_code = 241526

    @mute_logger("py.warnings")
    def test_00_sendcloud_integration_wizards(self):
        with recorder.use_cassette("update_integration"):
            self.integration.write(
                {
                    "shop_name": "Sendcloud API Integration",
                    "service_point_enabled": False,
                }
            )
        integrations = (
            self.env["sendcloud.integration"].with_context(active_test=False).search([])
        )
        self.assertFalse(integrations.service_point_carrier_ids)
        integrations.unlink()
        sendcloud_sync_order_wizard_rec = self.env[
            "sendcloud.sync.order.wizard"
        ].create({})
        sendcloud_sync_wizard_rec = self.env["sendcloud.sync.wizard"].create({})
        with self.assertRaisesRegex(
            UserError,
            "No Sendcloud integrations found. Setup an integration first.",
        ):
            sendcloud_sync_order_wizard_rec.button_sync()
        with self.assertRaisesRegex(
            UserError,
            "No Sendcloud integrations found. Setup an integration first.",
        ):
            sendcloud_sync_wizard_rec.button_sync()
        form = Form(self.env["sendcloud.integration.wizard"])
        wizard = form.save()
        self.assertRegex(
            wizard.base_url, self.env["sendcloud.request"]._param_web_base_url()
        )
        self.assertFalse(wizard.is_sendcloud_test_mode)
        wizard.base_url = "https://f482-185-247-144-87.eu.ngrok.io"
        self.assertRegex(
            wizard.integration_request_url, "f482-185-247-144-87.eu.ngrok.io"
        )

    @mute_logger("py.warnings")
    def test_01_sender_address(self):
        sender_address_obj = self.env["sendcloud.sender.address"]
        sender_address_obj.search([]).unlink()
        self.assertFalse(sender_address_obj.search([]))
        sendcloud_sync_wizard_rec = self.env["sendcloud.sync.wizard"].create(
            {
                "brands": False,
                "returns": False,
                "parcel_statuses": False,
                "parcels": False,
                "invoices": False,
                "sender_addresses": True,
                "shipping_methods": False,
            }
        )
        with recorder.use_cassette("sender_address"):
            sendcloud_sync_wizard_rec.button_sync()
        self.assertEqual(len(sender_address_obj.search([])), 2)

    @mute_logger("py.warnings")
    def test_02_hs_code(self):
        """Retrieve Sendcloud shipping methods.
        Harmonized System Code is mandatory when shipping outside of EU
        """
        sendcloud_sync_order_wizard_rec = self.env[
            "sendcloud.sync.order.wizard"
        ].create({})
        with self.assertRaisesRegex(
            UserError,
            "There are no outgoing shipments set with Sendcloud shipping method.",
        ):
            sendcloud_sync_order_wizard_rec.button_sync()
        delivery_carrier_obj = self.env["delivery.carrier"]

        @contextmanager
        def rollback():
            savepoint = self.cr.savepoint()
            yield
            savepoint.rollback()

        # Not any Sendcloud shipping method
        delivery_carrier_obj.search([("delivery_type", "=", "sendcloud")]).unlink()
        shipping_methods = delivery_carrier_obj.search(
            [("delivery_type", "=", "sendcloud")], limit=1
        )
        self.assertFalse(shipping_methods)

        # Retrieve Sendcloud shipping methods
        with recorder.use_cassette("shipping_methods"):
            delivery_carrier_obj.sendcloud_sync_shipping_method()
        shipping_method0 = delivery_carrier_obj.search(
            [("delivery_type", "=", "sendcloud")], limit=1
        )
        self.assertTrue(shipping_method0)
        # To test updation of existing records
        with recorder.use_cassette("shipping_methods"):
            delivery_carrier_obj.sendcloud_sync_shipping_method()
        # Sale order to outside EU
        self._setup_sendcloud_sender_address()
        sale_order = self._create_sendcloud_sale_order()
        europe_codes = self.env.ref("base.europe").country_ids.mapped("code")
        partner_country = sale_order.partner_id.country_id.code
        sale_order.partner_id.street_number2 = "test"
        self.assertFalse(partner_country in europe_codes)

        # Feature "Auto create invoice" not enabled by default
        self.assertFalse(sale_order.company_id.sendcloud_auto_create_invoice)
        # Set Sendcloud Price
        shipping_method0.sendcloud_price = 100.0
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
        with rollback():
            # HS code consistency
            with self.assertRaisesRegex(
                ValidationError,
                "Harmonized System Code is mandatory when shipping outside of EU",
            ):
                sale_order.with_context(
                    force_sendcloud_shipment_code="c9b2058d-2621-4ce5-afb0-f14e8e5565b6"
                ).action_confirm()
        # Set HS code and confirm order
        is_product_harmonized_system_installed = self.env["ir.module.module"].search(
            [("name", "=", "product_harmonized_system"), ("state", "=", "installed")],
            limit=1,
        )
        if is_product_harmonized_system_installed:
            sale_order.mapped("order_line.product_id").write(
                {"hs_code_id": self.env.ref("product_harmonized_system.84715000").id}
            )
        else:
            sale_order.mapped("order_line.product_id").write({"hs_code": "123"})
        with rollback():
            # Origin Country consistency
            with self.assertRaisesRegex(
                ValidationError,
                "Origin Country is mandatory when shipping outside of EU and to "
                "some states.",
            ):
                sale_order.with_context(
                    force_sendcloud_shipment_code="c9b2058d-2621-4ce5-afb0-f14e8e5565b6"
                ).action_confirm()
        shipping_method0.sendcloud_price = 0.0
        # Set country_of_origin and confirm order
        if is_product_harmonized_system_installed:
            sale_order.mapped("order_line.product_id").write(
                {"origin_country_id": sale_order.warehouse_id.partner_id.country_id}
            )
        else:
            sale_order.mapped("order_line.product_id").write(
                {"country_of_origin": sale_order.warehouse_id.partner_id.country_id}
            )
        with recorder.use_cassette("shipping_02"):
            sale_order.with_context(
                force_sendcloud_shipment_code="c9b2058d-2621-4ce5-afb0-f14e8e5565b6"
            ).action_confirm()
        # Not any invoice is created
        self.assertEqual(len(sale_order.invoice_ids), 0)

    def test_03_retrieve_integrations(self):
        with recorder.use_cassette("integrations"):
            self.integration.action_sendcloud_update_integrations()

    def test_04_auto_create_invoice(self):
        # Sale order to outside EU and "Auto create invoice" enabled
        self._setup_sendcloud_accounting()
        sale_order = self._create_sendcloud_sale_order()
        self.assertEqual(sale_order.partner_id.country_id.code, "US")
        sale_order.company_id.sendcloud_auto_create_invoice = True

        # No pre-existing invoices
        out_invoices = sale_order.invoice_ids.filtered(
            lambda i: i.move_type == "out_invoice"
        )
        self.assertFalse(out_invoices)

        out_invoices = sale_order._sendcloud_order_invoice()

        # Invoices created
        self.assertEqual(len(out_invoices), 1)
        self.assertEqual(out_invoices.move_type, "out_invoice")
        self.assertEqual(out_invoices.state, "posted")

    def test_05_retrieve_brands(self):
        sendcloud_brand_obj = self.env["sendcloud.brand"]
        sendcloud_brand_obj.search([]).unlink()
        self.assertFalse(sendcloud_brand_obj.search([]))
        sendcloud_sync_wizard_rec = self.env["sendcloud.sync.wizard"].create(
            {
                "brands": True,
                "returns": False,
                "parcel_statuses": False,
                "parcels": False,
                "invoices": False,
                "sender_addresses": False,
                "shipping_methods": False,
            }
        )
        with recorder.use_cassette("brands"):
            sendcloud_sync_wizard_rec.button_sync()
        self.assertEqual(len(sendcloud_brand_obj.search([])), 1)

    def test_06_retrieve_returns(self):
        sendcloud_return_obj = self.env["sendcloud.return"]
        sendcloud_return_obj.search([]).unlink()
        self.assertFalse(sendcloud_return_obj.search([]))
        sendcloud_sync_wizard_rec = self.env["sendcloud.sync.wizard"].create(
            {
                "brands": False,
                "returns": True,
                "parcel_statuses": False,
                "parcels": False,
                "invoices": False,
                "sender_addresses": False,
                "shipping_methods": False,
            }
        )
        with recorder.use_cassette("returns"):
            sendcloud_sync_wizard_rec.button_sync()
        # To test updation of existing returns
        with recorder.use_cassette("returns"):
            sendcloud_sync_wizard_rec.button_sync()
        sendcloud_return_rec = sendcloud_return_obj.search([], limit=1)
        self.assertTrue(sendcloud_return_rec)
        with recorder.use_cassette("parcels"):
            self.env["sendcloud.parcel.status"].sendcloud_sync_parcel_statuses()
            self.env["sendcloud.parcel"].sendcloud_sync_parcels()
        self.assertFalse(sendcloud_return_rec.outgoing_parcel_id)
        self.assertTrue(sendcloud_return_rec.incoming_parcel_id)

    def test_07_retrieve_parcels_and_statuses(self):
        sendcloud_parcel_obj = self.env["sendcloud.parcel"]
        sendcloud_parcel_status_obj = self.env["sendcloud.parcel.status"]
        sendcloud_parcel_status_obj.search([]).unlink()
        self.assertFalse(sendcloud_parcel_status_obj.search([]))
        sendcloud_parcel_obj.search([]).unlink()
        self.assertFalse(sendcloud_parcel_obj.search([]))
        with recorder.use_cassette("brands"):
            self.env["sendcloud.brand"].sendcloud_sync_brands()
        with recorder.use_cassette("shipping_methods"):
            self.env["delivery.carrier"].sendcloud_sync_shipping_method()
        sendcloud_sync_wizard_rec = self.env["sendcloud.sync.wizard"].create(
            {
                "brands": False,
                "returns": False,
                "parcel_statuses": True,
                "parcels": True,
                "invoices": False,
                "sender_addresses": False,
                "shipping_methods": False,
            }
        )
        with recorder.use_cassette("parcels"):
            sendcloud_sync_wizard_rec.button_sync()
        # To test updation of existing returns
        with recorder.use_cassette("parcels"):
            sendcloud_sync_wizard_rec.button_sync()
        with recorder.use_cassette("statuses"):
            sendcloud_parcel_status_obj.sendcloud_sync_parcel_statuses()
        self.assertTrue(len(sendcloud_parcel_status_obj.search([])))
        sendcloud_parcel_rec = sendcloud_parcel_obj.search(
            [("sendcloud_code", "=", 182588401)]
        )
        sendcloud_parcel_rec.action_parcel_documents()
        self.assertTrue(sendcloud_parcel_rec.document_ids)
        self.assertTrue(sendcloud_parcel_rec.shipment_id)
        self.assertTrue(sendcloud_parcel_rec.company_id)
        with recorder.use_cassette("parcel"):
            sendcloud_parcel_rec.button_sync_parcel()
        self.assertRegex(
            sendcloud_parcel_rec.action_create_return_parcel()["context"],
            str(sendcloud_parcel_rec.id),
        )
        with self.assertRaisesRegex(
            UserError, "Label not available: no label printer url provided."
        ):
            sendcloud_parcel_rec.action_get_parcel_label()
        sendcloud_parcel_rec.label_printer_url = "https://panel.sendcloud.sc/api/v2"
        sendcloud_parcel_rec.action_get_parcel_label()
        with self.assertRaisesRegex(
            UserError, "Document not available: no link provided."
        ):
            sendcloud_parcel_rec.document_ids.action_get_parcel_document()
        with recorder.use_cassette("cancel_parcel_182588401"):
            sendcloud_parcel_rec.with_context(skip_raise_error_401=True).unlink()

    def test_08_retrieve_invoices(self):
        sendcloud_invoice_obj = self.env["sendcloud.invoice"]
        sendcloud_invoice_obj.search([]).unlink()
        self.assertFalse(sendcloud_invoice_obj.search([]))
        sendcloud_sync_wizard_rec = self.env["sendcloud.sync.wizard"].create(
            {
                "brands": False,
                "returns": False,
                "parcel_statuses": False,
                "parcels": False,
                "invoices": True,
                "sender_addresses": False,
                "shipping_methods": False,
            }
        )
        with recorder.use_cassette("invoices"):
            sendcloud_sync_wizard_rec.button_sync()
        # To test updation of existing invoices
        with recorder.use_cassette("invoices"):
            sendcloud_sync_wizard_rec.button_sync()
        sendcloud_invoice = self.env["sendcloud.invoice"].search(
            [("sendcloud_code", "=", 718097)]
        )
        self.assertTrue(sendcloud_invoice)
        with recorder.use_cassette("invoice"):
            sendcloud_invoice.button_get_invoice_details()

    def test_09_warehouse_address_wizard(self):
        """No error is raised"""
        sendcloud_warehouse_address_wizard_obj = self.env[
            "sendcloud.warehouse.address.wizard"
        ]
        sendcloud_sender_address_obj = self.env["sendcloud.sender.address"]
        form = Form(sendcloud_warehouse_address_wizard_obj)
        wizard = form.save()
        wizard.button_update()
        # A partner outside the countries the sender addresses are in, so that
        # the wizard reports the mismatch below.
        partner_id = self._create_sendcloud_partner()
        with recorder.use_cassette("sender_address"):
            sendcloud_sender_address_obj.sendcloud_sync_sender_address()
        # To test updation of existing sender addresses
        with recorder.use_cassette("sender_address"):
            sendcloud_sender_address_obj.sendcloud_sync_sender_address()
        sender_address_id = sendcloud_sender_address_obj.search([], limit=1).id
        partner_id.sencloud_sender_address_id = sender_address_id
        self.env["stock.warehouse"].create(
            {
                "name": "WH 2",
                "code": "WH2",
                "company_id": self.env.company.id,
                "partner_id": partner_id.id,
            }
        )
        form = Form(sendcloud_warehouse_address_wizard_obj)
        wizard = form.save()
        with self.assertRaisesRegex(
            ValidationError,
            "Inconsistent countries",
        ):
            wizard.button_update()

    @mute_logger("py.warnings")
    def test_10_auto_create_invoice(self):
        """Test the "Auto create invoice" feature: when shipping outside EU"""
        # Sale order to outside EU
        self._setup_sendcloud_accounting()
        sale_order = self._create_sendcloud_sale_order()
        self.assertEqual(sale_order.partner_id.country_id.code, "US")
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

        # Enable "Auto create invoice"
        sale_order.company_id.sendcloud_auto_create_invoice = True
        self.env.ref("delivery_sendcloud_oca.sendcloud_product_delivery").unlink()
        # retrieve Sendcloud shipping methods
        sendcloud_sync_wizard_rec = self.env["sendcloud.sync.wizard"].create(
            {
                "brands": False,
                "returns": False,
                "parcel_statuses": False,
                "parcels": False,
                "invoices": False,
                "sender_addresses": False,
                "shipping_methods": True,
            }
        )
        with recorder.use_cassette("shipping_methods"):
            sendcloud_sync_wizard_rec.button_sync()
        shipping_method0 = self.env["delivery.carrier"].search(
            [("delivery_type", "=", "sendcloud"), ("sendcloud_code", "=", 9)], limit=1
        )
        self.assertTrue(shipping_method0.can_generate_return)
        with recorder.use_cassette("shipping_method"):
            shipping_method0.button_from_sendcloud_sync()
        shipping_method0.sendcloud_service_point_input = "required"
        self.assertFalse(shipping_method0.is_sendcloud_test_mode)
        with self.assertRaisesRegex(
            ValidationError,
            "The company is mandatory when delivery carrier is Sendcloud.",
        ):
            shipping_method0.company_id = False
        with self.assertRaisesRegex(
            ValidationError,
            "The company is not consistent with the integration company.",
        ):
            shipping_method0.company_id = 2
        shipping_method0.company_id = self.env.company.id
        shipping_method0._compute_sendcloud_country_ids()
        # Set Sendcloud delivery method
        choose_delivery_form = Form(
            self.env["choose.delivery.carrier"]
            .with_context(
                **{
                    "default_carrier_id": shipping_method0.id,
                }
            )
            .create({"order_id": sale_order.id})
        )
        choose_delivery_wizard = choose_delivery_form.save()
        choose_delivery_wizard.button_confirm()

        # No pre-existing invoices
        out_invoices = sale_order.invoice_ids.filtered(
            lambda i: i.move_type == "out_invoice"
        )
        self.assertFalse(out_invoices)

        # Confirm order
        with recorder.use_cassette("shipping_01"):
            with (
                self.assertRaisesRegex(
                    ValidationError, "Sendcloud Service Point is Required"
                ),
                self.cr.savepoint(),
            ):
                sale_order.with_context(
                    force_sendcloud_shipment_code="bfdebf74-853d-4c32-9484-e0201426f888"
                ).action_confirm()
            shipping_method0.sendcloud_service_point_input = "none"
            sale_order.with_context(
                force_sendcloud_shipment_code="bfdebf74-853d-4c32-9484-e0201426f888"
            ).action_confirm()
        with recorder.use_cassette("shipping_01"):
            sale_order.button_to_sendcloud_sync()
        # Invoice automatically created
        self.assertEqual(len(sale_order.invoice_ids), 1)
        self.assertEqual(sale_order.invoice_ids.move_type, "out_invoice")
        self.assertEqual(sale_order.invoice_ids.state, "posted")
        sale_order._compute_sendcloud_sp_details()
        sale_order.picking_ids._compute_sendcloud_sp_details()
        self.assertRegex(
            sale_order.picking_ids.action_open_sendcloud_parcels()["res_model"],
            "sendcloud.parcel",
        )
        sale_order.picking_ids.action_download_sendcloud_labels()
        with recorder.use_cassette("shipping_01"):
            sale_order.picking_ids.button_to_sendcloud_sync()
        with recorder.use_cassette("create_parcel"):
            sale_order.picking_ids.with_context(
                force_sendcloud_order_code="58e6e33e-a952-4b8e-afdd-4cddeaf4f665"
            ).action_multi_create_sendcloud_labels_download()
        self.assertEqual(sale_order.picking_ids.sendcloud_parcel_count, 1)
        with recorder.use_cassette("create_parcel"):
            shipping_method0.sendcloud_send_shipping(sale_order.picking_ids)
        with recorder.use_cassette("create_parcel"):
            sale_order.picking_ids._sendcloud_send_shipping()
        self.assertEqual(
            sale_order.picking_ids.cancel_shipment()["xml_id"],
            "delivery_sendcloud_oca.sendcloud_cancel_shipment_confirm_wizard",
        )
        with self.assertRaisesRegex(UserError, "Sendcloud"):
            sale_order.action_cancel()
        with self.assertRaisesRegex(UserError, "Sendcloud"):
            sale_order.button_delete_sendcloud_order()
        sendcloud_cancel_shipment_confirm_wizard_form = Form(
            self.env["sendcloud.cancel.shipment.confirm.wizard"].with_context(
                active_id=sale_order.picking_ids.ids[0], active_model="stock.picking"
            )
        )
        sendcloud_cancel_shipment_confirm_wizard_form = (
            sendcloud_cancel_shipment_confirm_wizard_form.save()
        )
        with recorder.use_cassette("cancel_parcel"):
            sendcloud_cancel_shipment_confirm_wizard_form.do_cancel_shipment()
        with self.assertRaisesRegex(UserError, "Sendcloud"):
            sale_order.picking_ids.button_delete_sendcloud_picking()
        with self.assertRaisesRegex(UserError, "Sendcloud"):
            sale_order.picking_ids.action_cancel()
        with self.assertRaisesRegex(UserError, "Sendcloud"):
            sale_order.picking_ids.unlink()
        shipping_method0.sendcloud_get_return_label(sale_order.picking_ids)
        sale_order.with_context(disable_cancel_warning=True).action_cancel()
        sale_order.unlink()

    @mute_logger("py.warnings")
    def test_11_set_custom_price_wizard(self):
        delivery_carrier_obj = self.env["delivery.carrier"]
        with recorder.use_cassette("shipping_methods"):
            delivery_carrier_obj.sendcloud_sync_shipping_method()
        delivery_carrier_obj._compute_sendcloud_service_point_required()
        sendcloud_shipping_method_country_obj = self.env[
            "sendcloud.shipping.method.country"
        ]
        shipping_method_country_rec = sendcloud_shipping_method_country_obj.search(
            [], limit=1
        )
        self.assertEqual(shipping_method_country_rec.price_check, "standard")
        self.assertEqual(
            shipping_method_country_rec.from_country_id, self.env.ref("base.nl")
        )
        self.assertRegex(
            shipping_method_country_rec.sendcloud_custom_price_details()["res_model"],
            "sendcloud.custom.price.details.wizard",
        )
        sendcloud_custom_price_details_wizard_rec = self.env[
            "sendcloud.custom.price.details.wizard"
        ].create(
            {
                "shipping_method_country_id": shipping_method_country_rec.id,
                "price_custom": 8.0,
            }
        )
        sendcloud_custom_price_details_wizard_rec.set_custom_price()
        self.assertEqual(shipping_method_country_rec.price_custom, 8.0)
        sendcloud_custom_price_details_wizard_rec.remove_custom_price()
        self.assertFalse(
            sendcloud_custom_price_details_wizard_rec.search(
                [("id", "=", shipping_method_country_rec.id)]
            )
        )

    @mute_logger("py.warnings")
    def test_12_create_return_parcel_wizard(self):
        sendcloud_brand_obj = self.env["sendcloud.brand"]
        with recorder.use_cassette("brands"):
            sendcloud_brand_obj.sendcloud_sync_brands()
        sendcloud_brand = sendcloud_brand_obj.search([], limit=1)
        self.assertRegex(sendcloud_brand.return_portal_url, "shipping-portal.com/rp/")
        self.assertRegex(
            sendcloud_brand.action_create_return_parcel()["context"],
            str(sendcloud_brand.id),
        )
        sendcloud_create_return_parcel_wizard_rec = self.env[
            "sendcloud.create.return.parcel.wizard"
        ].create(
            {
                "line_ids": [(0, 0, {"sendcloud_code": "182588401", "quantity": 1})],
                "postal_code": "4814dc",
                "identifier": "JVGL06097547001969761800",
                "brand_id": sendcloud_brand.id,
            }
        )
        sendcloud_create_return_parcel_wizard_rec._onchange_configuration()
        sendcloud_create_return_parcel_wizard_rec.button_confirm()
        with recorder.use_cassette("outgoing_parcel"):
            sendcloud_create_return_parcel_wizard_rec._step1(self.integration)

    @mute_logger("py.warnings")
    def test_13_sendcloud_country_specific_product(self):
        delivery_carrier_obj = self.env["delivery.carrier"]
        test_partner = self.env["res.partner"].create(
            {
                "name": "test",
                "country_id": self.env.ref("base.nl").id,
                "street": "Bloemstraat 42",
                "zip": "4817RH",
                "city": "Groningen",
                "phone": "+31 6 12345678",
                "state_id": self.env.ref("base.state_nl_gr").id,
                "email": "admin@yourcompany.example.com",
            }
        )
        sale_order = self._create_sendcloud_sale_order()
        sale_order.partner_id = test_partner.id
        # Retrieve Sendcloud shipping methods
        with recorder.use_cassette("shipping_methods"):
            delivery_carrier_obj.sendcloud_sync_shipping_method()
        delivery_product = self.env["product.product"].create(
            {"name": "Sendcloud Delivery", "type": "service"}
        )
        shipping_method0 = delivery_carrier_obj.search(
            [("delivery_type", "=", "sendcloud")], limit=1
        )
        self.env["sendcloud.shipping.method.country"].search(
            [
                ("iso_2", "=", test_partner.country_id.code),
                ("company_id", "=", self.env.company.id),
                ("method_code", "=", shipping_method0.sendcloud_code),
            ],
            limit=1,
        ).write({"product_id": delivery_product.id})
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
        self.assertTrue(delivery_product in sale_order.mapped("order_line.product_id"))

    @mute_logger("py.warnings")
    def test_14_sendcloud_onboarding(self):
        onboarding_onboarding_step_obj = self.env["onboarding.onboarding.step"]
        onboarding_onboarding_obj = self.env["onboarding.onboarding"]
        self.assertEqual(
            onboarding_onboarding_step_obj.action_open_sendcloud_onboarding_integration()[
                "res_model"
            ],
            "sendcloud.integration.wizard",
        )
        self.assertEqual(
            onboarding_onboarding_step_obj.action_sendcloud_onboarding_sync()[
                "res_model"
            ],
            "sendcloud.sync.wizard",
        )
        self.assertEqual(
            onboarding_onboarding_step_obj.action_open_sendcloud_onboarding_warehouse_address()[
                "res_model"
            ],
            "sendcloud.warehouse.address.wizard",
        )
        self.assertTrue(onboarding_onboarding_obj.get_sendcloud_onboarding_data())
        onboarding_onboarding_obj.action_close_sendcloud_onboarding()

    @mute_logger("py.warnings")
    def test_15_sendcloud_action(self):
        sendcloud_action_obj = self.env["sendcloud.action"]
        sendcloud_action_rec = sendcloud_action_obj.create(
            {
                "company_id": self.env.company.id,
                "message_type": "received",
                "message": "Error",
            }
        )
        sendcloud_action_rec._compute_resource_record()
        sendcloud_action_rec.parse_result()
        # Should generate an error on receiving message which is not in json format
        self.assertTrue(sendcloud_action_rec.error_on_parsing)
        sendcloud_action_obj.sendcloud_delete_old_actions()

    @responses.activate
    def test_16_sendcloud_integration_failure(self):
        responses.add(
            responses.POST,
            "https://localhost/shop/sendcloud_integration_webhook/1",
            json={"error": "not found"},
            status=300,
        )
        form = Form(self.env["sendcloud.integration.wizard"])
        wizard = form.save()
        wizard.base_url = "https://localhost"
        wizard.button_update()

    @responses.activate
    def test_17_sendcloud_integration_success(self):
        responses.add(
            responses.POST,
            "https://f482-185-247-144-87.eu.ngrok.io/shop/sendcloud_integration_webhook/1",
            json={"success": "true"},
            status=200,
        )
        form = Form(self.env["sendcloud.integration.wizard"])
        wizard = form.save()
        wizard.base_url = "https://f482-185-247-144-87.eu.ngrok.io"
        wizard.button_update()

    @responses.activate
    def test_18_sendcloud_integration_request_errors(self):
        responses.add(
            responses.GET,
            "https://panel.sendcloud.sc/api/v2/integrations",
            json={"error": {"message": "500 Server Error"}},
            status=500,
        )
        with self.assertRaises(UserError):
            self.integration.action_sendcloud_update_integrations()
        responses.reset()
        responses.add(
            responses.GET,
            "https://panel.sendcloud.sc/api/v2/integrations",
            json={"error": {"message": "504 Server Error"}},
            status=504,
        )
        with self.assertRaises(UserError):
            self.integration.action_sendcloud_update_integrations()
        responses.reset()
        responses.add(
            responses.GET,
            "https://panel.sendcloud.sc/api/v2/integrations",
            body=requests.exceptions.Timeout("Timeout"),
            status=408,
        )
        with self.assertRaises(UserError):
            self.integration.action_sendcloud_update_integrations()
        responses.reset()
        responses.add(
            responses.GET,
            "https://panel.sendcloud.sc/api/v2/integrations",
            body=requests.exceptions.ConnectionError("Connection Error"),
            status=503,
        )
        with self.assertRaises(UserError):
            self.integration.action_sendcloud_update_integrations()

    def test_19_sendcloud_available_carriers(self):
        delivery_carrier_obj = self.env["delivery.carrier"]
        test_partner = self.env["res.partner"].create(
            {
                "name": "test",
                "country_id": self.env.ref("base.nl").id,
                "street": "Bloemstraat 42",
                "zip": "4817RH",
                "city": "Groningen",
                "phone": "+31 6 12345678",
                "state_id": self.env.ref("base.state_nl_gr").id,
                "email": "admin@yourcompany.example.com",
            }
        )
        sale_order = self._create_sendcloud_sale_order()
        sale_order.partner_id = test_partner.id
        # Retrieve Sendcloud shipping methods
        with recorder.use_cassette("shipping_methods"):
            delivery_carrier_obj.sendcloud_sync_shipping_method()
        shipping_method0 = delivery_carrier_obj.search(
            [
                ("sendcloud_is_return", "=", True),
                ("company_id", "=", self.env.company.id),
            ],
            limit=1,
        )
        self.assertFalse(shipping_method0._is_available_for_order(sale_order))
        shipping_method1 = delivery_carrier_obj.search(
            [
                ("delivery_type", "=", "sendcloud"),
                ("sendcloud_min_weight", ">", 15.00),
                ("company_id", "=", self.env.company.id),
            ],
            limit=1,
        )
        self.assertFalse(shipping_method1._is_available_for_order(sale_order))
        with recorder.use_cassette("update_integration_2"):
            self.integration.write(
                {"service_point_enabled": True, "service_point_carriers": "['postnl']"}
            )
        shipping_method2 = delivery_carrier_obj.search(
            [
                ("delivery_type", "=", "sendcloud"),
                ("sendcloud_service_point_input", "=", "required"),
                ("sendcloud_carrier", "=", "dhl"),
                ("company_id", "=", self.env.company.id),
            ],
            limit=1,
        )
        self.assertFalse(shipping_method2._is_available_for_order(sale_order))
        shipping_method3 = delivery_carrier_obj.search(
            [
                ("delivery_type", "=", "sendcloud"),
                ("sendcloud_min_weight", "=", 0.001),
                ("company_id", "=", self.env.company.id),
            ],
            limit=1,
        )
        self.assertFalse(shipping_method3._is_available_for_order(sale_order))
        sale_order.warehouse_id.sencloud_sender_address_id = False
        self.assertFalse(shipping_method3._is_available_for_order(sale_order))
        self.assertTrue(
            self.env.ref("delivery.free_delivery_carrier")._is_available_for_order(
                sale_order
            )
        )

    def test_20_selection_helpers(self):
        """The selections the parcel and invoice views are built from."""
        mixin = self.env["sendcloud.mixin"]
        shipment_types = mixin._get_sendcloud_customs_shipment_type()
        self.assertIn(("2", "Commercial Goods"), shipment_types)
        invoice_types = self.env["sendcloud.invoice"]._selection_invoice_type()
        self.assertIn(("periodic", "Periodical"), invoice_types)

    def test_21_price_converted_from_euro(self):
        """Sendcloud quotes in euro, so other currencies are converted."""
        currency_obj = self.env["res.currency"].with_context(active_test=False)
        euro = currency_obj.search([("name", "=", "EUR")], limit=1)
        self.assertTrue(euro, "Sendcloud prices are quoted in euro")
        euro.active = True
        pricelist_obj = self.env["product.pricelist"]
        order = self._create_sendcloud_sale_order()
        # Priced in euro already: Sendcloud's price is taken as it is.
        order.pricelist_id = pricelist_obj.create(
            {"name": "Sendcloud EUR", "currency_id": euro.id}
        )
        self.assertEqual(order._sendcloud_convert_price_in_euro(10.0), 10.0)
        # Priced in anything else: the euro amount is converted into it.
        dollar = self.env.ref("base.USD")
        dollar.active = True
        order.pricelist_id = pricelist_obj.create(
            {"name": "Sendcloud USD", "currency_id": dollar.id}
        )
        self.assertEqual(
            order._sendcloud_convert_price_in_euro(10.0),
            euro._convert(10.0, dollar, order.company_id, order.date_order),
        )

    @mute_logger("py.warnings")
    def test_22_rate_needs_a_country(self):
        """An address with no country cannot be quoted."""
        delivery_carrier_obj = self.env["delivery.carrier"]
        with recorder.use_cassette("shipping_methods"):
            delivery_carrier_obj.sendcloud_sync_shipping_method()
        carrier = delivery_carrier_obj.search(
            [("delivery_type", "=", "sendcloud")], limit=1
        )
        partner = self.env["res.partner"].create({"name": "Nowhere in particular"})
        order = self._create_sendcloud_sale_order(partner=partner)
        res = carrier.sendcloud_rate_shipment(order)
        self.assertFalse(res["success"])
        self.assertEqual(res["error_message"], "Partner does not have any country.")
        # The delivery wizard surfaces that instead of a rate.
        wizard = self.env["choose.delivery.carrier"].create(
            {"order_id": order.id, "carrier_id": carrier.id}
        )
        self.assertEqual(
            wizard._onchange_carrier_id().get("error"),
            "Partner does not have any country.",
        )

    def test_23_parcel_document(self):
        """A document needs a link, and is always stored as a PDF."""
        document_obj = self.env["sendcloud.parcel.document"]
        document = document_obj.create({"name": "customs", "size": "1"})
        with self.assertRaisesRegex(UserError, "no link provided"):
            document.action_get_parcel_document()
        self.assertEqual(document.generate_parcel_document_filename(), "customs.pdf")
        document.name = "customs.pdf"
        self.assertEqual(document.generate_parcel_document_filename(), "customs.pdf")

    @mute_logger("odoo.addons.delivery_sendcloud_oca.models.stock_picking")
    def test_24_shipment_confirmations(self):
        """Sendcloud answers with one status per shipment it was sent."""
        picking = self._create_sendcloud_picking()
        picking.sendcloud_shipment_uuid = "uuid-1"

        def confirm(*confirmations):
            return patch.object(
                type(self.integration), "create_shipments", return_value=confirmations
            )

        # Created: the shipment is now known to Sendcloud.
        picking.sendcloud_last_cached = False
        with confirm({"status": "created", "shipment_uuid": "uuid-1"}):
            err_msg = picking._sync_shipment_to_sendcloud("", self.integration, {})
        self.assertFalse(err_msg)
        self.assertTrue(picking.sendcloud_last_cached)

        # Updated: an already known shipment keeps its uuid.
        picking.sendcloud_last_cached = False
        with confirm({"status": "updated", "shipment_uuid": "uuid-1"}):
            err_msg = picking._sync_shipment_to_sendcloud("", self.integration, {})
        self.assertFalse(err_msg)
        self.assertEqual(picking.sendcloud_shipment_uuid, "uuid-1")
        self.assertTrue(picking.sendcloud_last_cached)

        # Error: collected into the message the caller raises.
        error = {
            "status": "error",
            "shipment_uuid": "uuid-1",
            "error": {"external_order_id": "SO1", "external_shipment_id": "SH1"},
        }
        with confirm(error):
            err_msg = picking._sync_shipment_to_sendcloud("", self.integration, {})
        self.assertIn("SO1", err_msg)
        self.assertIn("SH1", err_msg)

    @mute_logger("py.warnings")
    def test_25_service_point_is_checked_on_done_pickings(self):
        """A delivered parcel must carry the service point it was sold with."""
        delivery_carrier_obj = self.env["delivery.carrier"]
        with recorder.use_cassette("shipping_methods"):
            delivery_carrier_obj.sendcloud_sync_shipping_method()
        carrier = delivery_carrier_obj.search(
            [("delivery_type", "=", "sendcloud"), ("sendcloud_is_return", "=", False)],
            limit=1,
        )
        carrier.sendcloud_service_point_input = "required"
        carrier.sendcloud_integration_id = self.integration
        integration = self.integration.with_context(skip_update_in_sendcloud=True)
        integration.service_point_enabled = False

        picking = self._create_sendcloud_picking()
        product = self.env["product.product"].create(
            {"name": "Shipped thing", "type": "consu", "weight": 0.01}
        )
        self.env["stock.move"].create(
            {
                "product_id": product.id,
                "product_uom_qty": 1,
                "picking_id": picking.id,
                "location_id": picking.location_id.id,
                "location_dest_id": picking.location_dest_id.id,
            }
        )
        picking.action_confirm()
        picking.move_ids.quantity = 1
        picking.move_ids.picked = True
        picking.button_validate()
        self.assertEqual(picking.state, "done")

        @contextmanager
        def rollback():
            savepoint = self.cr.savepoint()
            yield
            savepoint.rollback()

        with rollback():
            with self.assertRaisesRegex(
                ValidationError, "Sendcloud Service Point is required."
            ):
                picking.carrier_id = carrier
        picking.sendcloud_service_point_address = '{"id": 1}'
        with rollback():
            with self.assertRaisesRegex(
                ValidationError, "Service Point not enabled for this integration"
            ):
                picking.carrier_id = carrier
        integration.service_point_enabled = True
        integration.service_point_carriers = "['postnl']"
        carrier.sendcloud_carrier = "dhl"
        with rollback():
            with self.assertRaisesRegex(
                ValidationError, "Carrier not enabled for this integration"
            ):
                picking.carrier_id = carrier

    def test_26_return_parcel_refund_and_reason_are_required(self):
        """The return portal refuses a parcel without a refund and a reason."""
        brand = self.env["sendcloud.brand"].create(
            {"name": "Test brand", "sendcloud_code": 1, "domain": "testbrand"}
        )
        parcel = self.env["sendcloud.parcel"].create(
            {
                "name": "182588401",
                "sendcloud_code": 182588401,
                "address": "Reduitlaan 45",
                "city": "Breda",
                "country_iso_2": "NL",
                "postal_code": "4814DC",
                "partner_name": "Acme Corporation",
                "company_id": self.env.company.id,
            }
        )
        wizard = self.env["sendcloud.create.return.parcel.wizard"].create(
            {
                "postal_code": "4814DC",
                "identifier": "JVGL06097547001969761800",
                "brand_id": brand.id,
                "parcel_id": parcel.id,
                "access_token": "token",
                "line_ids": [(0, 0, {"sendcloud_code": "182588401", "quantity": 1})],
            }
        )
        with self.assertRaisesRegex(UserError, "Refund option is required"):
            wizard._step2(self.integration)

        refund_option_obj = self.env[
            "sendcloud.create.return.parcel.wizard.refund.option"
        ]
        wizard.refund_option_id = refund_option_obj.create(
            {"name": "Money", "code": "money", "require_message": True}
        )
        with self.assertRaisesRegex(UserError, "Refund message is required"):
            wizard._step2(self.integration)

        # Without items, the return needs a reason of its own.
        wizard.refund_message = "Broken on arrival"
        wizard.line_ids.unlink()
        with self.assertRaisesRegex(UserError, "Reason is required"):
            wizard._step2(self.integration)

    def _create_sendcloud_parcel(self, picking, code, **values):
        parcel_values = {
            "name": str(code),
            "sendcloud_code": code,
            "picking_id": picking.id,
            "company_id": self.env.company.id,
        }
        parcel_values.update(values)
        return self.env["sendcloud.parcel"].create(parcel_values)

    def test_27_label_print_status(self):
        """A transfer reports the state its parcel labels agree on."""
        picking = self._create_sendcloud_picking()
        self.assertFalse(picking.label_print_status)
        first = self._create_sendcloud_parcel(picking, 1)
        second = self._create_sendcloud_parcel(picking, 2)
        self.assertEqual(picking.label_print_status, "generated")
        second.label_print_status = "printed"
        self.assertEqual(picking.label_print_status, "partial")
        first.label_print_status = "printed"
        self.assertEqual(picking.label_print_status, "printed")

    def test_28_parcel_creation_is_reported(self):
        """Sendcloud refusing the parcels stops the transfer."""
        picking_obj = self.env["stock.picking"]

        def answer(response):
            return patch.object(
                type(self.integration), "create_parcels", return_value=response
            )

        with answer({"error": {"message": "no such shipping method"}}):
            with self.assertRaisesRegex(UserError, "no such shipping method"):
                picking_obj._sendcloud_sync_multiple_parcels(self.integration, [])

        failed = {"failed_parcels": [{"parcel": {"id": 1}, "errors": "too heavy"}]}
        with answer(failed):
            with self.assertRaisesRegex(UserError, "too heavy"):
                picking_obj._sendcloud_sync_multiple_parcels(self.integration, [])

        with answer({"parcels": [{"id": 1}]}):
            parcels = picking_obj._sendcloud_sync_multiple_parcels(self.integration, [])
        self.assertEqual(parcels, [{"id": 1}])

    @mute_logger("py.warnings")
    def test_29_cancel_shipment_outcomes(self):
        """Sendcloud has several ways of saying a parcel is gone."""
        delivery_carrier_obj = self.env["delivery.carrier"]
        with recorder.use_cassette("shipping_methods"):
            delivery_carrier_obj.sendcloud_sync_shipping_method()
        carrier = delivery_carrier_obj.search(
            [("delivery_type", "=", "sendcloud")], limit=1
        )
        picking = self._create_sendcloud_picking()

        def answer(response):
            return patch.object(
                type(self.integration), "cancel_parcel", return_value=response
            )

        already_cancelled = {
            "status": "failed",
            "message": "This shipment is already being cancelled.",
        }
        gone = ({"status": "deleted"}, already_cancelled, {"error": {"code": 404}})
        for code, response in enumerate(gone, start=1):
            self._create_sendcloud_parcel(picking, code)
            with answer(response):
                carrier.sendcloud_cancel_shipment(picking)
            self.assertFalse(picking.sendcloud_parcel_ids)

        # Any other error leaves the parcel alone and stops the cancellation.
        self._create_sendcloud_parcel(picking, 4)
        with answer({"error": {"code": 400, "message": "still in transit"}}):
            with self.assertRaisesRegex(ValidationError, "still in transit"):
                carrier.sendcloud_cancel_shipment(picking)

    def test_30_return_parcel_is_created(self):
        """A confirmed return brings back a Sendcloud return and its parcels."""
        brand = self.env["sendcloud.brand"].create(
            {"name": "Test brand", "sendcloud_code": 1, "domain": "testbrand"}
        )
        picking = self._create_sendcloud_picking()
        parcel = self._create_sendcloud_parcel(
            picking,
            182588401,
            address="Reduitlaan 45",
            city="Breda",
            country_iso_2="NL",
            postal_code="4814DC",
            partner_name="Acme Corporation",
        )
        wizard_obj = self.env["sendcloud.create.return.parcel.wizard"]
        wizard = wizard_obj.create(
            {
                "postal_code": "4814DC",
                "identifier": "JVGL06097547001969761800",
                "brand_id": brand.id,
                "parcel_id": parcel.id,
                "access_token": "token",
                "collo_count": 1,
                "line_ids": [
                    (0, 0, {"sendcloud_code": "182588401", "quantity": 1, "price": 5.0})
                ],
            }
        )
        refund_option_obj = self.env[
            "sendcloud.create.return.parcel.wizard.refund.option"
        ]
        wizard.refund_option_id = refund_option_obj.create(
            {"name": "Money", "code": "money"}
        )
        delivery_option_obj = self.env[
            "sendcloud.create.return.parcel.wizard.delivery.option"
        ]
        wizard.delivery_option_id = delivery_option_obj.create(
            {"code": "drop_off_point"}
        )

        integration_cls = type(self.integration)
        incoming_code = 999888
        with (
            patch.object(
                integration_cls,
                "create_return_portal_incoming_parcel",
                return_value={
                    "return": 1910013,
                    "incoming_parcels": [incoming_code],
                    "poller_url": "https://panel.sendcloud.sc/poll/1",
                },
            ),
            patch.object(
                integration_cls,
                "get_return",
                return_value={"id": 1910013, "message": "", "status": "created"},
            ),
            patch.object(
                integration_cls,
                "get_parcel",
                return_value={"id": incoming_code, "carrier": {"code": "postnl"}},
            ),
        ):
            sendcloud_return = wizard._step2(self.integration)

        self.assertEqual(sendcloud_return.sendcloud_code, 1910013)
        self.assertEqual(wizard.poller_url, "https://panel.sendcloud.sc/poll/1")
        incoming = self.env["sendcloud.parcel"].search(
            [("sendcloud_code", "=", incoming_code)]
        )
        self.assertEqual(incoming.picking_id, picking)

    @responses.activate
    def test_31_request_layer(self):
        """The corners of the Sendcloud HTTP layer."""
        base = "https://panel.sendcloud.sc/api/v2"

        # Rate limited once, then served.
        responses.add(responses.GET, f"{base}/returns/1", json={}, status=429)
        responses.add(responses.GET, f"{base}/returns/1", json={"id": 1}, status=200)
        self.assertEqual(self.integration.get_return(1), {"id": 1})

        # An error body carrying nothing but a bare message.
        responses.add(
            responses.GET, f"{base}/returns/2", json={"message": "nope"}, status=502
        )
        with self.assertRaisesRegex(UserError, "nope"):
            self.integration.get_return(2)

        # Bad credentials are raised while the response is being logged.
        responses.add(
            responses.GET,
            f"{base}/returns/3",
            json={"error": {"message": "invalid key"}},
            status=401,
        )
        with self.assertRaisesRegex(UserError, "invalid key"):
            self.integration.get_return(3)

        # The return portal, which is addressed by brand rather than by code.
        responses.add(
            responses.GET,
            f"{base}/brand/testbrand/return-portal",
            json={"portal": {}},
            status=200,
        )
        self.assertEqual(
            self.integration.get_return_portal_settings("testbrand", language="en"),
            {"portal": {}},
        )
        responses.add(
            responses.POST,
            f"{base}/brand/testbrand/return-portal/incoming",
            json={"return": 1},
            status=200,
        )
        self.assertEqual(
            self.integration.create_return_portal_incoming_parcel(
                "testbrand", {}, {"Authorization": "Bearer token"}
            ),
            {"return": 1},
        )

    @responses.activate
    def test_32_parcel_document_is_downloaded(self):
        """A parcel document is fetched and kept as an attachment."""
        link = "https://panel.sendcloud.sc/api/v2/documents/1"
        responses.add(responses.GET, link, body=b"%PDF-1.3 customs", status=200)
        picking = self._create_sendcloud_picking()
        parcel = self._create_sendcloud_parcel(picking, 1)
        document = self.env["sendcloud.parcel.document"].create(
            {"name": "customs-form", "parcel_id": parcel.id, "link": link}
        )
        document.action_get_parcel_document()
        self.assertEqual(document.attachment_id.name, "customs-form.pdf")
        self.assertEqual(
            base64.b64decode(document.attachment_id.datas), b"%PDF-1.3 customs"
        )

    @responses.activate
    def test_33_action_log_finds_the_parcel(self):
        """A parcel webhook is matched back to the transfer that shipped it."""
        responses.add(
            responses.GET,
            "https://panel.sendcloud.sc/api/v2/parcels/3/return_portal_url",
            json={"url": "https://testbrand.shipping-portal.com/rp/"},
            status=200,
        )
        action_obj = self.env["sendcloud.action"]
        self.assertTrue(action_obj._reference_models())
        picking = self._create_sendcloud_picking()
        parcel = self._create_sendcloud_parcel(picking, 3)
        action = action_obj.create(
            {
                "company_id": self.env.company.id,
                "sendcloud_integration_id": self.integration.id,
                "message_type": "received",
                "action": "parcel_status_changed",
                "message": json.dumps(
                    {
                        "action": "parcel_status_changed",
                        "parcel": {
                            "id": 3,
                            "external_order_id": "",
                            "external_shipment_id": "",
                            "status": {"id": 1000, "message": "Ready to send"},
                        },
                    }
                ),
            }
        )
        action.reparse_message()
        self.assertEqual(action.model, parcel._name)
        self.assertEqual(action.record_id, parcel)

    @mute_logger("py.warnings")
    def test_34_picking_label_and_delete_actions(self):
        """The Sendcloud buttons on the transfer form."""
        picking = self._create_sendcloud_picking()
        # Nothing has been labelled yet, so there is nothing to download.
        self.assertFalse(picking.action_download_sendcloud_labels())
        attachment = self.env["ir.attachment"].create(
            {"name": "label.pdf", "datas": base64.b64encode(MINIMAL_PDF)}
        )
        self._create_sendcloud_parcel(picking, 1, attachment_id=attachment.id)
        action = picking.action_download_sendcloud_labels()
        self.assertEqual(action["type"], "ir.actions.act_url")
        self.assertIn(str(picking.id), action["url"])
        # A transfer Sendcloud never saw is cancelled and deleted on its own.
        untouched = self._create_sendcloud_picking()
        self.assertFalse(untouched.to_delete_sendcloud_pickings())
        untouched.action_cancel()
        untouched.unlink()

    def test_35_exact_price_of_parcel(self):
        """The parcel price is looked up from the country it ships to."""
        delivery_carrier_obj = self.env["delivery.carrier"]
        with recorder.use_cassette("shipping_methods"):
            delivery_carrier_obj.sendcloud_sync_shipping_method()
        carrier = delivery_carrier_obj.search(
            [("delivery_type", "=", "sendcloud")], limit=1
        )
        order = self._create_sendcloud_sale_order()
        order.carrier_id = carrier
        picking = self._create_sendcloud_picking(partner=order.partner_id)
        picking.sale_id = order
        parcel_data = {"external_reference": f"{picking.name},1"}
        self.assertIsInstance(picking._get_exact_price_of_parcel(parcel_data), float)
        # Without a country there is no price to look up.
        order.partner_id.country_id = False
        self.assertEqual(picking._get_exact_price_of_parcel(parcel_data), 0.0)

    @responses.activate
    def test_36_response_shapes(self):
        """Not every Sendcloud answer is a JSON body."""
        base = "https://panel.sendcloud.sc/api/v2"
        # A "No Content" answer has nothing to read.
        responses.add(responses.GET, f"{base}/returns/4", status=204)
        self.assertEqual(self.integration.get_return(4), {})
        # A body that is not JSON at all is reported rather than raised.
        responses.add(responses.GET, f"{base}/returns/5", body="not json", status=200)
        res = self.integration.get_return(5)
        self.assertEqual(res["error"]["code"], "JSONDecodeError")
        # The parcel status selection is built from the synced statuses.
        statuses = self.env["sendcloud.parcel"]._selection_parcel_statuses()
        self.assertIsInstance(statuses, list)

    @responses.activate
    def test_37_parcel_portal_url_and_cancellation(self):
        """A parcel knows its return portal, and refuses to vanish silently."""
        base = "https://panel.sendcloud.sc/api/v2"
        picking = self._create_sendcloud_picking()
        parcel = self._create_sendcloud_parcel(picking, 7)
        self.assertEqual(parcel._generate_parcel_label_filename(), "7.pdf")

        # Sendcloud has a portal for this parcel.
        responses.add(
            responses.GET,
            f"{base}/parcels/7/return_portal_url",
            json={"url": "https://testbrand.shipping-portal.com/rp/"},
            status=200,
        )
        parcel.action_get_return_portal_url()
        self.assertEqual(
            parcel.return_portal_url, "https://testbrand.shipping-portal.com/rp/"
        )
        # And has none for this one.
        responses.reset()
        responses.add(
            responses.GET,
            f"{base}/parcels/7/return_portal_url",
            json={"url": None},
            status=200,
        )
        parcel.action_get_return_portal_url()
        self.assertEqual(parcel.return_portal_url, "None")

        def cancelling(response):
            return patch.object(
                type(self.integration), "cancel_parcel", return_value=response
            )

        # A parcel Sendcloud will not cancel stays where it is.
        with cancelling({"error": {"code": 400, "message": "already in transit"}}):
            with self.assertRaisesRegex(UserError, "already in transit"):
                parcel.unlink()
        # One Sendcloud has never heard of is simply dropped.
        with cancelling({"error": {"code": 404, "message": "not found"}}):
            parcel.unlink()
        self.assertFalse(parcel.exists())
