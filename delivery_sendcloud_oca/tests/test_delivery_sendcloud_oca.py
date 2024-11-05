# Copyright 2022 Onestein (<https://www.onestein.nl>)
# License OPL-1 (https://www.odoo.com/documentation/16.0/legal/licenses.html#odoo-apps).

import logging
from contextlib import contextmanager
from os.path import dirname, join

import requests
from vcr import VCR

from odoo.exceptions import UserError, ValidationError
from odoo.tests import Form, TransactionCase
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


class TestDeliverySendCloud(TransactionCase):
    @classmethod
    def _request_handler(cls, s, r, /, **kw):
        """Don't block external requests."""
        return _super_send(s, r, **kw)

    @mute_logger("py.warnings")
    def setUp(self):
        super().setUp()
        if not self.registry.in_test_mode():
            self.registry.enter_test_mode(self.cr)
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

    @classmethod
    def tearDownClass(self):
        self.registry.leave_test_mode()
        super().tearDownClass()

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
        sale_order = self.env.ref("sale.sale_order_1").copy()
        europe_codes = self.env.ref("base.europe").country_ids.mapped("code")
        partner_country = sale_order.partner_id.country_id.code
        self.assertFalse(partner_country in europe_codes)

        # Feature "Auto create invoice" not enabled by default
        self.assertFalse(sale_order.company_id.sendcloud_auto_create_invoice)

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
        sale_order = self.env.ref("sale.sale_order_1").copy()
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
        partner_id = self.env.ref("base.res_partner_2")
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
        sale_order = self.env.ref("sale.sale_order_1").copy()
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
        self.assertFalse(shipping_method0.is_sendcloud_test_mode)
        with self.assertRaisesRegex(
            ValidationError,
            "The company is mandatory when delivery carrier is Sendcloud.",
        ):
            shipping_method0.company_id = False
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
        with self.assertRaisesRegex(UserError, "Sendcloud: Invalid username/password"):
            sale_order.action_cancel()
        with self.assertRaisesRegex(UserError, "Sendcloud: Invalid username/password"):
            sale_order.button_delete_sendcloud_order()
        sendcloud_cancel_shipment_confirm_wizard_form = Form(
            self.env["sendcloud.cancel.shipment.confirm.wizard"].with_context(
                **{
                    "active_id": sale_order.picking_ids.ids[0],
                    "active_model": "stock.picking",
                }
            )
        )
        sendcloud_cancel_shipment_confirm_wizard_form = (
            sendcloud_cancel_shipment_confirm_wizard_form.save()
        )
        with recorder.use_cassette("cancel_parcel"):
            sendcloud_cancel_shipment_confirm_wizard_form.do_cancel_shipment()
        with self.assertRaisesRegex(UserError, "Sendcloud: Invalid username/password"):
            sale_order.picking_ids.button_delete_sendcloud_picking()
        with self.assertRaisesRegex(UserError, "Sendcloud: Invalid username/password"):
            sale_order.picking_ids.action_cancel()
        with self.assertRaisesRegex(UserError, "Sendcloud: Invalid username/password"):
            sale_order.picking_ids.unlink()

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
        sale_order = self.env.ref("sale.sale_order_1").copy()
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
        self.env["onboarding.onboarding"].action_close_sendcloud_onboarding()

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
