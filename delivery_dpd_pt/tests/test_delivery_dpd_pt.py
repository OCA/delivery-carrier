# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64
from unittest import mock

from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestDeliveryDPDPortugal(TransactionCase):
    """Test DPD Portugal delivery carrier functionality."""

    def setUp(self):
        """Set up test data."""
        super().setUp()

        self.customer = self.env["res.partner"].create(
            {
                "name": "Test Customer",
                "street": "Test Street 123",
                "city": "Lisbon",
                "zip": "1000-001",
                "country_id": self.env.ref("base.pt").id,
                "email": "customer@test.com",
                "phone": "+351 912 345 678",
            }
        )
        self.sender = self.env["res.partner"].create(
            {
                "name": "Test Sender",
                "country_id": self.env.ref("base.pt").id,
                "email": "sender@test.com",
                "phone": "+351 212 345 678",
            }
        )
        self.warehouse_partner = self.env["res.partner"].create(
            {
                "name": "Test Warehouse",
                "street": "Warehouse Street 1",
                "city": "Porto",
                "zip": "4000-001",
                "country_id": self.env.ref("base.pt").id,
            }
        )
        self.env.ref("stock.warehouse0").partner_id = self.warehouse_partner

        self.carrier_account = self.env["carrier.account"].create(
            {
                "name": "DPD Test Account",
                "delivery_type": "dpd_pt",
                "account": "dpd-user",
                "password": "dpd-password",
                "dpd_pt_client_id": "132",
                "dpd_pt_client_secret": "dpd-client-secret",
            }
        )
        self.dpd_carrier = self.env["delivery.carrier"].create(
            {
                "name": "DPD Portugal Test",
                "delivery_type": "dpd_pt",
                "dpd_pt_subaccount": "12345678",
                "dpd_pt_sender_id": self.sender.id,
                "dpd_pt_price": 5.0,
                "product_id": self.env.ref("delivery.product_product_delivery").id,
            }
        )
        self.dpd_carrier.carrier_account_id = self.carrier_account

    def _make_picking(self, tracking_ref=False):
        picking = self.env["stock.picking"].create(
            {
                "partner_id": self.customer.id,
                "picking_type_id": self.env.ref("stock.picking_type_out").id,
                "location_id": self.env.ref("stock.stock_location_stock").id,
                "location_dest_id": self.env.ref("stock.stock_location_customers").id,
                "carrier_id": self.dpd_carrier.id,
                "carrier_tracking_ref": tracking_ref,
            }
        )
        picking.shipping_weight = 2.5
        return picking

    def _json_response(self, payload, status_code=200):
        response = mock.Mock()
        response.status_code = status_code
        response.content = b"{}"
        response.headers = {"Content-Type": "application/json"}
        response.json.return_value = payload
        return response

    def _token_response(self):
        return self._json_response(
            {"access_token": "TOKEN", "token_type": "Bearer", "expires_in": 3600}
        )

    def _create_response(self, result):
        return self._json_response(
            {
                "status_code": 200,
                "message": "Expedição registada.",
                "result": result,
            }
        )

    def _pdf_result(self, **extra):
        result = {
            "num_guia": "098359060015735",
            "guias_seur": [],
            "pdf": base64.b64encode(b"%PDF-1.4 label").decode(),
        }
        result.update(extra)
        return result

    def _post_side_effect(self, create_result):
        def post(url, **kwargs):
            if url.endswith("/oauth/token"):
                return self._token_response()
            if url.endswith("/expedition/registarExpedicao"):
                return self._create_response(create_result)
            raise AssertionError(f"Unexpected POST URL: {url}")

        return post

    def test_carrier_creation(self):
        """A DPD Portugal carrier is created with its configuration."""
        self.assertEqual(self.dpd_carrier.delivery_type, "dpd_pt")
        self.assertEqual(self.dpd_carrier.dpd_pt_subaccount, "12345678")
        self.assertFalse(self.dpd_carrier.prod_environment)
        self.assertFalse(self.dpd_carrier.can_generate_return)

    def test_rate_shipment_uses_agreed_price(self):
        """Rating returns the agreed DPD price; the API has no rating."""
        if "sale.order" not in self.env:
            self.skipTest("sale module is not installed")
        order = self.env["sale.order"].create({"partner_id": self.customer.id})
        result = self.dpd_carrier.dpd_pt_rate_shipment(order)
        self.assertTrue(result["success"])
        self.assertEqual(result["price"], 5.0)

    def test_tracking_link_production_only(self):
        """A tracking link is provided for production shipments only."""
        picking = self._make_picking("123456789A,987654321B")

        # Test environment: no public tracking link.
        self.assertFalse(self.dpd_carrier.dpd_pt_get_tracking_link(picking))

        # Production: link targets the first guide number.
        self.dpd_carrier.prod_environment = True
        link = self.dpd_carrier.dpd_pt_get_tracking_link(picking)
        self.assertIn("tracking.dpd.pt", link)
        self.assertIn("123456789A", link)
        self.assertNotIn("987654321B", link)

    def test_send_shipping_uses_spec_oauth_and_payload(self):
        """A shipment is registered after a form-encoded OAuth password grant."""
        picking = self._make_picking()
        with mock.patch(
            "odoo.addons.delivery_dpd_pt.models.delivery_carrier.requests.post"
        ) as post_mock:
            post_mock.side_effect = self._post_side_effect(self._pdf_result())
            result = self.dpd_carrier.dpd_pt_send_shipping(picking)

        self.assertEqual(result[0]["tracking_number"], "098359060015735")
        token_call, create_call = post_mock.call_args_list
        self.assertEqual(
            token_call.args[0], "https://qabusiness.dpd.pt/api/v1/pt/oauth/token"
        )
        self.assertEqual(
            token_call.kwargs["data"],
            {
                "username": "dpd-user",
                "password": "dpd-password",
                "client_id": "132",
                "client_secret": "dpd-client-secret",
                "grant_type": "password",
            },
        )
        self.assertEqual(
            create_call.args[0],
            "https://qabusiness.dpd.pt/api/v1/pt/expedition/registarExpedicao",
        )
        self.assertEqual(create_call.kwargs["headers"]["Authorization"], "Bearer TOKEN")
        payload = create_call.kwargs["json"]
        self.assertEqual(payload["sub_account"], {"code": "12345678"})
        self.assertEqual(payload["encomenda_peso_envio"], 2.5)
        self.assertEqual(payload["encomenda_num_volumes"], 1)
        self.assertTrue(payload["pdf_response"])
        self.assertFalse(payload["zpl_response"])
        contact = payload["contact"]
        self.assertEqual(contact["phone"], "912345678")
        self.assertEqual(contact["phone_code"], "+351")
        self.assertEqual(contact["mobile"], "912345678")
        self.assertEqual(contact["mobile_code"], "+351")
        sender = payload["sender"]
        self.assertEqual(sender["phone"], "212345678")
        self.assertEqual(sender["mobile"], "212345678")
        self.assertEqual(sender["email"], "sender@test.com")

    def test_send_shipping_keeps_all_multi_parcel_guide_numbers(self):
        """A multi-parcel shipment keeps the guide numbers returned by DPD."""
        picking = self._make_picking()
        picking.number_of_packages = 2
        create_result = self._pdf_result(
            num_guia="MASTER123456",
            guias_seur=["MASTER123456", "SECOND123456"],
        )
        with mock.patch(
            "odoo.addons.delivery_dpd_pt.models.delivery_carrier.requests.post"
        ) as post_mock:
            post_mock.side_effect = self._post_side_effect(create_result)
            result = self.dpd_carrier.dpd_pt_send_shipping(picking)

        self.assertEqual(result[0]["tracking_number"], "MASTER123456,SECOND123456")
        payload = post_mock.call_args_list[1].kwargs["json"]
        self.assertEqual(payload["encomenda_num_volumes"], 2)

    def test_cancel_uses_master_guide_and_string_ids(self):
        """Cancelling a multi-parcel shipment uses only the master guide ID."""
        picking = self._make_picking("MASTER123456,SECOND123456")

        def post(url, **kwargs):
            if url.endswith("/oauth/token"):
                return self._token_response()
            if url.endswith("/expedition/cancelar"):
                return self._json_response(
                    {"status_code": 200, "message": "OK", "result": None}
                )
            raise AssertionError(f"Unexpected POST URL: {url}")

        with (
            mock.patch(
                "odoo.addons.delivery_dpd_pt.models.delivery_carrier.requests.post"
            ) as post_mock,
            mock.patch(
                "odoo.addons.delivery_dpd_pt.models.delivery_carrier.requests.get"
            ) as get_mock,
        ):
            post_mock.side_effect = post
            get_mock.return_value = self._json_response(
                {
                    "status_code": 200,
                    "message": "OK",
                    "result": {"id": 123, "num_guia": "MASTER123456"},
                }
            )
            self.dpd_carrier.dpd_pt_cancel_shipment(picking)

        self.assertEqual(get_mock.call_count, 1)
        self.assertTrue(get_mock.call_args.args[0].endswith("/guia/MASTER123456"))
        cancel_call = post_mock.call_args_list[-1]
        self.assertTrue(cancel_call.args[0].endswith("/expedition/cancelar"))
        self.assertEqual(cancel_call.kwargs["json"], {"ids": ["123"]})

    def test_shipper_is_null_when_warehouse_country_is_missing(self):
        """A warehouse without a country does not block the optional shipper."""
        self.warehouse_partner.country_id = False
        picking = self._make_picking()
        with mock.patch(
            "odoo.addons.delivery_dpd_pt.models.delivery_carrier.requests.post"
        ) as post_mock:
            post_mock.side_effect = self._post_side_effect(self._pdf_result())
            self.dpd_carrier.dpd_pt_send_shipping(picking)

        payload = post_mock.call_args_list[1].kwargs["json"]
        self.assertIsNone(payload["shipper"])

    def test_weight_above_dpd_format_is_rejected(self):
        """A shipment heavier than the API kkk.gg format is rejected."""
        picking = self._make_picking()
        picking.shipping_weight = 1000.0
        with self.assertRaises(UserError):
            self.dpd_carrier.dpd_pt_send_shipping(picking)

    def test_thermal_label_format_requests_and_stores_zpl(self):
        """A thermal shipment requests ZPL and attaches the printer label."""
        self.dpd_carrier.dpd_pt_label_format = "3"
        picking = self._make_picking()
        zpl = b"^XA^FO50,50^FDTest^FS^XZ"
        create_result = self._pdf_result(
            pdf=None,
            zpl=base64.b64encode(zpl).decode(),
        )
        with mock.patch(
            "odoo.addons.delivery_dpd_pt.models.delivery_carrier.requests.post"
        ) as post_mock:
            post_mock.side_effect = self._post_side_effect(create_result)
            self.dpd_carrier.dpd_pt_send_shipping(picking)

        payload = post_mock.call_args_list[1].kwargs["json"]
        self.assertFalse(payload["pdf_response"])
        self.assertTrue(payload["zpl_response"])
        attachment = self.env["ir.attachment"].search(
            [
                ("res_model", "=", "stock.picking"),
                ("res_id", "=", picking.id),
                ("name", "=like", "DPD_%.zpl"),
            ],
            limit=1,
        )
        self.assertTrue(attachment)
        self.assertEqual(attachment.raw, zpl)
