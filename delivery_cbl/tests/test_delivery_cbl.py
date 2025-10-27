# Copyright 2025 Ángel Rivas <angel.rivas@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64
from unittest.mock import MagicMock, Mock, patch

import requests
from markupsafe import Markup

from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase

from odoo.addons.delivery_cbl.models.cbl_request import CBLRequest


class TestCBLRequest(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.product = cls.env["product.product"].create(
            {
                "name": "CBL Delivery Product",
                "type": "service",
            }
        )
        cls.carrier = cls.env["delivery.carrier"].create(
            {
                "name": "CBL Carrier",
                "product_id": cls.product.id,
                "cbl_user": "test_user",
                "cbl_password": "test_password",
                "cbl_client_code": "test_client_code",
                "cbl_client_token": "test_client_token",
            }
        )
        cls.location_src = cls.env["stock.location"].create(
            {
                "name": "Source Location",
                "usage": "internal",
            }
        )
        cls.location_dest = cls.env["stock.location"].create(
            {
                "name": "Destination Location",
                "usage": "internal",
            }
        )
        cls.picking_type = cls.env["stock.picking.type"].create(
            {
                "name": "Test Picking Type",
                "code": "outgoing",
                "sequence_code": "OUT",
                "warehouse_id": cls.env["stock.warehouse"].search([], limit=1).id,
                "default_location_src_id": cls.location_src.id,
                "default_location_dest_id": cls.location_dest.id,
            }
        )
        cls.picking = cls.env["stock.picking"].create(
            {
                "name": "Test Picking",
                "location_id": cls.location_src.id,
                "location_dest_id": cls.location_dest.id,
                "picking_type_id": cls.picking_type.id,
            }
        )
        cls.cbl_request = CBLRequest(cls.carrier)

    def test_init(self):
        cbl_request = CBLRequest(self.carrier)
        self.assertEqual(cbl_request.user, self.carrier.cbl_user)
        self.assertEqual(cbl_request.password, self.carrier.cbl_password)
        self.assertEqual(cbl_request.client_code, self.carrier.cbl_client_code)
        self.assertEqual(cbl_request.client_token, self.carrier.cbl_client_token)

    def _send_request(self, op, url, headers, json=False):
        response = getattr(requests, op)(
            url,
            json=json,
            headers=headers,
        )
        return response

    @patch.object(requests, "get")
    def test_send_request_get(self, mock_get):
        cbl_request = CBLRequest(self.carrier)
        url = "https://example.com"
        headers = {"Authorization": f"Carrier {self.carrier.cbl_client_token}"}
        response = requests.Response()
        response.status_code = 200
        mock_get.return_value = response
        result = cbl_request._send_request("get", url, headers)
        self.assertEqual(result.status_code, response.status_code)

    @patch.object(requests, "post")
    def test_send_request_post(self, mock_post):
        cbl_request = CBLRequest(self.carrier)
        url = "https://example.com"
        headers = {"Authorization": "Bearer test_token"}
        response = MagicMock(status_code=200)
        mock_post.return_value = response
        result = cbl_request._send_request("post", url, headers)
        self.assertEqual(result, response)

    def test_manage_errors(self):
        cbl_request = CBLRequest(self.carrier)
        response = MagicMock(status_code=400, reason="Bad Request")
        with self.assertRaises(UserError):
            cbl_request._manage_errors(response, self.picking)

    def test_generate_auth(self):
        auth = self.cbl_request._generate_auth()
        self.assertIsInstance(auth, dict)
        self.assertIn("Authorization", auth)
        self.assertEqual(
            auth["Authorization"],
            "Basic "
            + base64.b64encode(
                f"{self.carrier.cbl_user}:{self.carrier.cbl_password}".encode("ascii")
            ).decode("utf-8"),
        )

    @patch.object(requests, "get")
    def test_generate_daily_token(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.reason = "OK"
        mock_response.json.return_value = {"dailyToken": "test_daily_token"}
        mock_get.return_value = mock_response
        daily_token = self.cbl_request._generate_daily_token(self.picking)
        self.assertIsInstance(daily_token, str)
        self.assertTrue(daily_token)

    def test_get_packages(self):
        packages = self.cbl_request._get_packages(self.picking)
        self.assertIsInstance(packages, list)
        self.assertTrue(packages)

    def test_generate_shipping_json_conditional_cash_on_delivery(self):
        self.carrier.cbl_cash_on_delivery = False
        self.picking.carrier_id = self.carrier
        self.picking.sale_id = None
        self.picking.company_id = self.env.company
        self.picking.partner_id = self.env["res.partner"].create(
            {
                "name": "Test Partner",
                "country_id": self.env.ref("base.es").id,
                "state_id": self.env["res.country.state"].search([], limit=1).id,
            }
        )
        self.picking.shipping_weight = 2.0
        daily_token = "dummy_token"
        json_data = self.cbl_request._generate_shipping_json(self.picking, daily_token)
        self.assertNotIn("cashOnDelivery", json_data)
        self.carrier.cbl_cash_on_delivery = True
        sale_order = self.env["sale.order"].create(
            {
                "partner_id": self.picking.partner_id.id,
            }
        )
        sale_order.amount_total = 99.99
        self.picking.sale_id = sale_order
        json_data = self.cbl_request._generate_shipping_json(self.picking, daily_token)
        self.assertAlmostEqual(json_data["cashOnDelivery"], 99.99, places=2)

    def test_send_shipping(self):
        cbl_request = CBLRequest(self.carrier)
        mock_daily_token = "mocked_token"
        mock_tracking_ref = "TRK123456"
        mock_packages_tags = [{"packageNumber": 1}]
        mocked_get_response = MagicMock(status_code=200)
        mocked_get_response.json.return_value = {"dailyToken": mock_daily_token}
        mocked_post_response = MagicMock(status_code=200)
        mocked_post_response.json.return_value = {
            "carrierReference": mock_tracking_ref,
            "packagesTags": mock_packages_tags,
        }
        with patch.object(
            cbl_request,
            "_send_request",
            side_effect=[mocked_get_response, mocked_post_response],
        ):
            self.picking.company_id = self.env["res.company"].create(
                {
                    "name": "Test Company",
                    "street": "Test Street",
                    "zip": "12345",
                    "city": "City",
                    "state_id": self.env.ref("base.state_es_b").id,
                    "country_id": self.env.ref("base.es").id,
                    "phone": "123456789",
                    "vat": "ESA12345678",
                    "email": "company@example.com",
                }
            )
            self.picking.partner_id = self.env["res.partner"].create(
                {
                    "name": "Customer",
                    "street": "Customer St",
                    "zip": "54321",
                    "city": "Customer City",
                    "state_id": self.env.ref("base.state_es_b").id,
                    "country_id": self.env.ref("base.es").id,
                    "phone": "987654321",
                    "vat": "ESB12345678",
                    "email": "customer@example.com",
                }
            )
            self.picking.carrier_id = self.carrier
            self.picking.shipping_weight = 1.0
            tracking_ref, packages_tags = cbl_request._send_shipping(self.picking)
            self.assertEqual(tracking_ref, mock_tracking_ref)
            self.assertEqual(packages_tags, mock_packages_tags)

    def test_cancel_shipment_confirmed(self):
        cbl_request = CBLRequest(self.carrier)
        self.picking.name = "PICK123"
        self.picking.cbl_confirmed = True
        self.picking.carrier_tracking_ref = "TRK123456"
        mock_token_response = MagicMock(status_code=200)
        mock_token_response.json.return_value = {"dailyToken": "mocked_token"}
        mock_delete_response = MagicMock(status_code=200)
        mock_delete_response.json.return_value = {"deletedShipments": 1}
        with patch.object(
            cbl_request,
            "_send_request",
            side_effect=[mock_token_response, mock_delete_response],
        ):
            deleted = cbl_request.cancel_shipment(self.picking)
            self.assertTrue(deleted)

    def test_confirm_shipments_success(self):
        cbl_request = CBLRequest(self.carrier)
        self.picking.name = "PICK456"
        self.picking.carrier_tracking_ref = "TRACK456"
        mock_token_response = MagicMock(status_code=200)
        mock_token_response.json.return_value = {"dailyToken": "mocked_token"}
        mock_confirm_response = MagicMock(status_code=200)
        mock_confirm_response.json.return_value = {"generatedShipments": 1}
        with patch.object(
            cbl_request,
            "_send_request",
            side_effect=[mock_token_response, mock_confirm_response],
        ):
            result = cbl_request.confirm_shipments(self.picking)
            self.assertTrue(result)

    def test_cbl_confirm_shipment(self):
        self.picking.carrier_tracking_ref = "TRK123456"
        self.picking.cbl_confirmed = False
        self.picking.delivery_type = "cbl"
        mock_response = MagicMock()
        mock_response.status_code = 200
        with patch.object(
            CBLRequest, "confirm_shipments", return_value=True
        ) as mock_confirm_shipments:
            self.carrier.cbl_confirm_shipment(
                self.env["stock.picking"].browse([self.picking.id])
            )
            mock_confirm_shipments.assert_called_once_with(self.picking)
            self.assertTrue(self.picking.cbl_confirmed)
            messages = [m.body for m in self.picking.message_ids]
            self.assertIn(Markup("<p>CBL Expedition confirmed.</p>"), messages)

    def test_cbl_confirm_shipment_cron(self):
        self.carrier.write(
            {
                "delivery_type": "cbl",
                "cbl_needs_confirmation": True,
            }
        )
        self.picking.write(
            {
                "carrier_id": self.carrier.id,
                "carrier_tracking_ref": "TRACK999",
                "cbl_confirmed": False,
            }
        )
        with patch.object(
            type(self.carrier), "cbl_confirm_shipment", autospec=True
        ) as mock_cbl_confirm:
            self.carrier.cbl_confirm_shipment_cron()
            mock_cbl_confirm.assert_called_once()
            called_pickings = mock_cbl_confirm.call_args[0][1]
            self.assertIn(self.picking, called_pickings)

    def test_wizard_default_get_excludes_invalid_pickings(self):
        confirmed_picking = self.picking.copy()
        confirmed_picking.write(
            {
                "carrier_id": self.carrier.id,
                "carrier_tracking_ref": "TRACK_CONFIRMED",
                "cbl_confirmed": True,
                "delivery_type": "cbl",
                "state": "done",
            }
        )
        draft_picking = self.picking.copy()
        draft_picking.write(
            {
                "carrier_id": self.carrier.id,
                "carrier_tracking_ref": "TRACK_DRAFT",
                "cbl_confirmed": False,
                "delivery_type": "cbl",
                "state": "assigned",
            }
        )
        Wizard = self.env["wizard.confirm.cbl.pickings"].with_context(
            default_picking_ids=[confirmed_picking.id, draft_picking.id]
        )
        defaults = Wizard.default_get(["picking_ids"])
        wizard = Wizard.create(defaults)
        self.assertNotIn(confirmed_picking.id, wizard.picking_ids.ids)
        self.assertNotIn(draft_picking.id, wizard.picking_ids.ids)

    def test_wizard_action_confirm_calls_carrier(self):
        self.carrier.write(
            {
                "delivery_type": "cbl",
                "cbl_needs_confirmation": True,
            }
        )
        self.picking.write(
            {
                "carrier_id": self.carrier.id,
                "carrier_tracking_ref": "TRACK456",
                "cbl_confirmed": False,
                "delivery_type": "cbl",
                "state": "done",
            }
        )
        wizard = self.env["wizard.confirm.cbl.pickings"].create(
            {
                "picking_ids": [(6, 0, [self.picking.id])],
            }
        )
        with patch.object(
            type(self.carrier), "cbl_confirm_shipment", autospec=True
        ) as mock_confirm:
            wizard.action_confirm_cbl_pickings()
            mock_confirm.assert_called_once()
            args = mock_confirm.call_args[0][1]
            self.assertIn(self.picking, args)

    def create_picking(self):
        return self.env["stock.picking"].create(
            {
                "name": "Test Picking",
                "location_id": self.location_src.id,
                "location_dest_id": self.location_dest.id,
                "picking_type_id": self.picking_type.id,
                "carrier_id": self.carrier.id,
            }
        )

    def test_generate_label_zpl(self):
        self.carrier.cbl_label_format = "zpl"
        picking = self.create_picking()

        labels_info = [
            {
                "tag": "ZPL_EXAMPLE_CONTENT",
                "sscc": "ABC123",
            }
        ]
        tracking_ref = "ZPL123"

        attachments = self.carrier.cdl_generate_labels(
            picking, tracking_ref, labels_info
        )

        self.assertEqual(len(attachments), 1)
        attachment = attachments[0]
        self.assertTrue(attachment.name.startswith("cbl_ZPL123_ABC123_1.zpl"))
        self.assertIn("ZPL_EXAMPLE_CONTENT", attachment.raw.decode("utf-8"))

    @patch("requests.post")
    def test_generate_label_pdf(self, mock_post):
        self.carrier.cbl_label_format = "pdf"
        picking = self.create_picking()

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b"%PDF-1.4 MOCKED PDF CONTENT"
        mock_post.return_value = mock_response

        labels_info = [
            {
                "tag": "ZPL_FOR_PDF",
                "sscc": "PDF999",
            }
        ]
        tracking_ref = "PDFTEST"

        attachments = self.carrier.cdl_generate_labels(
            picking, tracking_ref, labels_info
        )

        self.assertEqual(len(attachments), 1)
        attachment = attachments[0]
        self.assertTrue(attachment.name.startswith("cbl_PDFTEST_PDF999_1.pdf"))
        self.assertIn("%PDF-1.4", attachment.raw.decode("utf-8"))
