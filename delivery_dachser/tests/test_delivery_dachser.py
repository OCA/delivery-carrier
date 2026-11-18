# Copyright 2025 Tecnativa - Víctor Martínez
# Copyright 2026 Acysos S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import base64
from unittest.mock import MagicMock, patch

import requests

from odoo.exceptions import UserError
from odoo.tests import Form, tagged
from odoo.tools import mute_logger

from odoo.addons.delivery_dachser.models.dachser_master_data import (
    map_dachser_status_to_delivery_state,
)
from odoo.addons.delivery_dachser.models.dachser_request import DachserRequest

from .common import TestDeliveryDachserCommon

REQUEST_PATH = "odoo.addons.delivery_dachser.models.dachser_request.requests.request"


@tagged("post_install", "-at_install")
class TestDeliveryDachser(TestDeliveryDachserCommon):
    def _mock_response(self, status_code=200, json_data=None, text=""):
        resp = MagicMock()
        resp.status_code = status_code
        resp.text = text
        resp.content = b"{}" if json_data is not None else b""
        if json_data is not None:
            resp.json.return_value = json_data
        else:
            resp.json.side_effect = ValueError("No JSON")
        return resp

    def test_01_status_mapping_and_package_type_sync(self):
        """Test status mapper branches and StockPackageType code sync."""
        self.assertEqual(
            map_dachser_status_to_delivery_state("3500"), "customer_delivered"
        )
        self.assertEqual(map_dachser_status_to_delivery_state("9000"), "incident")
        self.assertEqual(map_dachser_status_to_delivery_state("X"), "canceled_shipment")
        self.assertEqual(
            map_dachser_status_to_delivery_state("9999", "Delivery exception: damage"),
            "incident",
        )
        self.assertEqual(
            map_dachser_status_to_delivery_state("9999", "Shipment zugestellt"),
            "customer_delivered",
        )
        self.assertEqual(
            map_dachser_status_to_delivery_state("9999", "Order cancelled / storniert"),
            "canceled_shipment",
        )
        self.assertEqual(
            map_dachser_status_to_delivery_state("9999", "Out for delivery at hub"),
            "in_transit",
        )
        self.assertEqual(
            map_dachser_status_to_delivery_state("9999", "Entry note"),
            "shipping_recorded_in_carrier",
        )

        pkg_type = self.env["stock.package.type"].create(
            {
                "name": "Dachser Half Pallet EP",
                "package_carrier_type": "dachser",
                "dachser_packaging_code": "EP",
            }
        )
        self.assertEqual(pkg_type.shipper_package_code, "EP")
        pkg_type.write({"dachser_packaging_code": "KT"})
        self.assertEqual(pkg_type.shipper_package_code, "KT")

        pkg_new = self.env["stock.package.type"].new(
            {
                "name": "Dachser Box Onchange",
                "package_carrier_type": "dachser",
                "dachser_packaging_code": "BX",
            }
        )
        pkg_new._onchange_dachser_packaging_code()
        self.assertEqual(pkg_new.shipper_package_code, "BX")

    @mute_logger("odoo.addons.delivery_dachser.models.dachser_request")
    @patch(REQUEST_PATH)
    def test_02_rate_shipment_wizard_currency_incoterms_and_errors(self, mock_req):
        """Test POST /rest/v2/quotations via standard wizard, USD conversion,
        Incoterm mapping, zero-weight fallback, and error responses.
        """
        incoterm_exw = self.env.ref("account.incoterm_EXW")
        self.sale_order.incoterm = incoterm_exw
        mock_req.return_value = self._mock_response(
            status_code=200,
            json_data={
                "id": "QUOT-2026-001",
                "totalAmount": {"amount": 78.50, "currency": "EUR"},
            },
        )
        action = self.sale_order.action_open_delivery_wizard()
        wiz = (
            self.env[action["res_model"]]
            .with_context(**action["context"])
            .create({"carrier_id": self.carrier.id})
        )
        wiz.update_price()
        self.assertAlmostEqual(wiz.display_price, 78.50, places=2)
        wiz.button_confirm()

        # USD currency conversion & zero-weight product fallback
        usd = self.env.ref("base.USD")
        usd.active = True
        zero_wt_product = self.env["product.product"].create(
            {"name": "Promo Leaflet", "type": "consu", "weight": 0.0}
        )
        order_form = Form(self.env["sale.order"])
        order_form.partner_id = self.partner
        with order_form.order_line.new() as line:
            line.product_id = zero_wt_product
            line.product_uom_qty = 2.0
        order2 = order_form.save()
        mock_req.return_value = self._mock_response(
            status_code=200,
            json_data={"totalAmount": {"amount": 100.0, "currency": "USD"}},
        )
        res_usd = self.carrier.dachser_rate_shipment(order2)
        self.assertTrue(res_usd["success"])
        self.assertGreater(res_usd["price"], 0.0)

        # Error branches: missing ZIP, HTTP 202 zero amount, HTTP 422 API error
        no_zip_partner = self.env["res.partner"].create(
            {"name": "No ZIP", "country_id": self.country_es.id}
        )
        order2.partner_shipping_id = no_zip_partner
        self.assertFalse(self.carrier.dachser_rate_shipment(order2)["success"])
        order2.partner_shipping_id = self.partner

        mock_req.return_value = self._mock_response(
            status_code=202, json_data={"totalAmount": {"amount": 0.0}}
        )
        self.assertFalse(self.carrier.dachser_rate_shipment(order2)["success"])

        mock_req.return_value = self._mock_response(
            status_code=422,
            json_data={"message": "No online tariff", "details": ["Contact branch"]},
        )
        self.assertFalse(self.carrier.dachser_rate_shipment(order2)["success"])

    @patch(REQUEST_PATH)
    def test_03_send_shipping_transportorder_packages_and_zpl(self, mock_req):
        """Test POST /rest/v2/transportorders/{basket} with physical packages,
        SSCC assignment, delivery_state fields, PDF & ZPL labels.
        """
        pkg = self.env["stock.quant.package"].create(
            {
                "name": "PACK-DACHSER-001",
                "package_type_id": self.package_type_eu.id,
            }
        )
        self.picking.move_line_ids.write({"result_package_id": pkg.id})
        self.sale_order.client_order_ref = "PO-2026-99"
        self.picking.note = "<p>Deliver at loading bay 2</p>"

        mock_req.return_value = self._mock_response(
            status_code=201,
            json_data={
                "id": 99001122,
                "state": "labelled",
                "ssccs": ["00340336850591178159"],
                "label": self.sample_pdf_b64,
            },
        )
        self.picking.send_to_shipper()
        self.assertEqual(self.picking.carrier_tracking_ref, "00340336850591178159")
        self.assertEqual(pkg.dachser_sscc, "00340336850591178159")
        self.assertEqual(self.picking.delivery_state, "shipping_recorded_in_carrier")
        self.assertEqual(self.picking.tracking_state_history, "labelled")
        self.assertEqual(
            self.picking.tracking_json.get("transport_order_id"), "99001122"
        )

        # Test ZPL mode without physical packages (using number_of_packages & volume)
        self.picking.move_line_ids.write({"result_package_id": False})
        self.picking.write({"number_of_packages": 2, "volume": 1.2})
        self.carrier.write(
            {
                "dachser_label_format": "Z",
                "dachser_font_file_name": "ARIALR.FNT",
                "dachser_order_group": "GRP-ZPL",
                "dachser_collection_time_from": "09:00",
                "dachser_collection_time_to": "17:00",
            }
        )
        zpl_b64 = base64.b64encode(b"^XA^FDZPL^FS^XZ").decode("ascii")
        mock_req.return_value = self._mock_response(
            status_code=201,
            json_data={
                "id": 99001123,
                "state": "sent",
                "ssccs": ["00340336850591178160"],
                "label": zpl_b64,
            },
        )
        ship_res = self.carrier.dachser_send_shipping(self.picking)
        self.assertEqual(ship_res[0]["tracking_number"], "00340336850591178160")
        zpl_att = self.env["ir.attachment"].search(
            [
                ("res_model", "=", "stock.picking"),
                ("res_id", "=", self.picking.id),
                ("name", "ilike", "%.zpl"),
            ]
        )
        self.assertTrue(zpl_att)

    @mute_logger("odoo.addons.delivery_dachser.models.dachser_request")
    @patch(REQUEST_PATH)
    def test_04_send_shipping_label_only_and_test_fallback(self, mock_req):
        """Test automatic fallback in test mode to POST /rest/v2/labels on 401
        and UserError on non-auth 500 failure.
        """
        unauth_resp = self._mock_response(status_code=401, text="Unauthorized")
        label_resp = self._mock_response(
            status_code=200,
            json_data={
                "ssccs": ["00340336850599999999"],
                "label": self.sample_pdf_b64,
                "relation": {"printableRelation": "193-005-DE"},
            },
        )
        mock_req.side_effect = [unauth_resp, label_resp]
        ship_res = self.carrier.dachser_send_shipping(self.picking)
        self.assertEqual(ship_res[0]["tracking_number"], "00340336850599999999")
        self.assertEqual(self.picking.tracking_json.get("ldr_routing"), "193-005-DE")

        mock_req.side_effect = None
        mock_req.return_value = self._mock_response(
            status_code=500, text="Internal Server Error"
        )
        with self.assertRaises(UserError):
            self.carrier.dachser_send_shipping(self.picking)

    @patch(REQUEST_PATH)
    def test_05_tms_confirm_reprint_label_and_return_label(self, mock_req):
        """Test dachser_send_to_tms, dachser_get_label, and return labels."""
        self.picking.write(
            {
                "carrier_tracking_ref": False,
                "tracking_json": {},
            }
        )
        self.assertFalse(self.picking.dachser_get_label())
        with self.assertRaises(UserError):
            self.picking.dachser_send_to_tms()

        self.picking.write(
            {
                "carrier_tracking_ref": "99001122",
                "tracking_state_history": "labelled",
                "tracking_json": {
                    "transport_order_id": "99001122",
                    "order_state": "labelled",
                },
            }
        )
        mock_req.return_value = self._mock_response(
            status_code=200,
            json_data={
                "id": 99001122,
                "state": "sent",
                "ssccs": ["00340336850591178159"],
                "label": self.sample_pdf_b64,
            },
        )
        self.picking.dachser_send_to_tms()
        self.assertEqual(self.picking.tracking_state_history, "sent")
        self.assertEqual(self.picking.carrier_tracking_ref, "00340336850591178159")

        # Reprint label from transport order ID and from standalone /labels
        self.carrier.dachser_label_format = "Z"
        self.picking.dachser_get_label()
        self.carrier.dachser_label_format = "P"
        self.picking.tracking_json = {"ssccs": ["00340336850591178159"]}
        self.picking.dachser_get_label()

        # Non-dachser carrier guards on StockPicking
        other_carrier = self.env["delivery.carrier"].create(
            {
                "name": "Fixed Carrier",
                "delivery_type": "fixed",
                "product_id": self.shipping_product.id,
            }
        )
        self.picking.carrier_id = other_carrier
        self.assertFalse(self.picking.dachser_get_label())
        self.assertFalse(self.picking.dachser_send_to_tms())
        self.picking.carrier_id = self.carrier

        # Return label generation
        mock_req.return_value = self._mock_response(
            status_code=200,
            json_data={
                "ssccs": ["00340336850590000001"],
                "label": self.sample_pdf_b64,
            },
        )
        self.carrier.dachser_get_return_label(self.picking)
        ret_att = self.env["ir.attachment"].search(
            [
                ("res_model", "=", "stock.picking"),
                ("res_id", "=", self.picking.id),
                ("name", "ilike", "dachser_return_%"),
            ]
        )
        self.assertTrue(ret_att)

    @mute_logger("odoo.addons.delivery_dachser.models.dachser_request")
    @patch(REQUEST_PATH)
    def test_06_tracking_state_update_pod_and_tracking_link(self, mock_req):
        """Test tracking link, tracking_state_update, event history, and POD."""
        self.picking.carrier_tracking_ref = False
        self.assertIsNone(self.carrier.dachser_tracking_state_update(self.picking))

        self.picking.carrier_tracking_ref = "00340336850591178159"
        link = self.carrier.dachser_get_tracking_link(self.picking)
        self.assertIn("00340336850591178159", link)

        # Empty response leaves delivery_state untouched
        empty_resp = self._mock_response(status_code=200, json_data=[])
        mock_req.side_effect = [empty_resp, empty_resp]
        self.picking.delivery_state = False
        self.picking.tracking_state_update()
        self.assertFalse(self.picking.delivery_state)

        # Swagger v2 list + history + automatic POD PDF download on delivery
        status_resp = self._mock_response(
            status_code=200,
            json_data=[
                {
                    "consignmentId": "81234567890",
                    "podSignor": "John Smith",
                    "status": {
                        "code": "3500",
                        "description": "Delivered",
                        "date": "2026-11-06T11:20:00",
                        "location": "Seville",
                    },
                }
            ],
        )
        history_resp = self._mock_response(
            status_code=200,
            json_data=[
                {
                    "consignmentId": "81234567890",
                    "status": [
                        {
                            "code": "1100",
                            "description": "Picked up",
                            "date": "2026-11-05T16:00:00",
                            "location": "Dos Hermanas",
                        },
                        {
                            "code": "3500",
                            "description": "Delivered",
                            "date": "2026-11-06T11:20:00",
                            "location": "Seville",
                        },
                    ],
                }
            ],
        )
        pod_resp = self._mock_response(
            status_code=200,
            json_data=[
                {
                    "consignmentId": "81234567890",
                    "podDocument": self.sample_pdf_b64,
                }
            ],
        )
        mock_req.side_effect = [status_resp, history_resp, pod_resp]
        self.picking.tracking_state_update()
        self.assertEqual(self.picking.delivery_state, "customer_delivered")
        self.assertTrue(self.picking.date_delivered)
        self.assertIn("John Smith", self.picking.tracking_state)
        self.assertIn("Picked up", self.picking.tracking_state_history)
        self.assertTrue(self.picking.pod_file)
        self.assertEqual(self.picking.pod_filename, "dachser_pod_81234567890.pdf")

        # OCA dict {"shipments": [...]} format with statusSequence & incident
        oca_status_resp = self._mock_response(
            status_code=200,
            json_data={
                "shipments": [
                    {
                        "consignmentId": "81234567890",
                        "status": [
                            {
                                "statusSequence": 1,
                                "statusDate": "2026-11-07",
                                "location": "Seville",
                                "reasonDescription": "Gate closed",
                                "event": {
                                    "code": "9000",
                                    "description": "Delivery exception",
                                },
                            },
                            {
                                "statusSequence": 2,
                                "statusDate": "2026-11-05",
                                "event": {"code": "1100", "description": "Picked up"},
                            },
                        ],
                    }
                ]
            },
        )
        mock_req.side_effect = [
            oca_status_resp,
            requests.exceptions.ConnectionError("History offline"),
        ]
        self.picking.tracking_state_update()
        self.assertEqual(self.picking.delivery_state, "incident")
        self.assertIn("Gate closed", self.picking.tracking_state)

    @mute_logger("odoo.addons.delivery_dachser.models.dachser_request")
    @patch(REQUEST_PATH)
    def test_07_cancel_shipment(self, mock_req):
        """Test DELETE /rest/v2/transportorders/{id} and sent blocking."""
        self.picking.write(
            {
                "carrier_tracking_ref": "00340336850591178159",
                "tracking_json": {
                    "transport_order_id": "99001122",
                    "order_state": "sent",
                },
            }
        )
        error_msg = (
            "It is not possible to cancel a shipment because it has already been sent."
        )
        with self.assertRaisesRegex(UserError, error_msg):
            self.picking.cancel_shipment()

        # API error when order was transmitted on Dachser side
        self.picking.tracking_json = {
            "transport_order_id": "99001122",
            "order_state": "labelled",
        }
        mock_req.return_value = self._mock_response(
            status_code=409, json_data={"message": "Already sent"}
        )
        with self.assertRaisesRegex(UserError, error_msg):
            self.picking.cancel_shipment()

        # Successful cancellation
        mock_req.return_value = self._mock_response(status_code=204, text="")
        self.picking.cancel_shipment()
        self.assertFalse(self.picking.carrier_tracking_ref)
        self.assertEqual(self.picking.delivery_state, "canceled_shipment")

    @mute_logger("odoo.addons.delivery_dachser.models.dachser_request")
    @patch(REQUEST_PATH)
    def test_08_transfer_list_wizard_and_request_helpers(self, mock_req):
        """Test daily Transfer List wizard, DachserRequest helpers, UoM/dimension
        fallbacks, Food division, partner validation, routing, and SSCC pool.
        """
        mock_req.return_value = self._mock_response(
            status_code=200,
            json_data={"document": self.sample_pdf_b64},
        )
        action = self.carrier.action_open_transfer_list_wizard()
        wiz = (
            self.env[action["res_model"]]
            .with_context(**action["context"])
            .create({"order_group": "GB"})
        )
        wiz.action_download_transfer_list()
        self.assertTrue(wiz.pdf_file)
        self.assertIn("Dachser_Manifest_", wiz.pdf_filename)

        # Empty manifest PDF, HTTP 429, Timeout, ConnectionError
        mock_req.return_value = self._mock_response(status_code=200, json_data={})
        with self.assertRaises(UserError):
            wiz.action_download_transfer_list()

        mock_req.return_value = self._mock_response(
            status_code=429, text="Too Many Requests"
        )
        with self.assertRaises(UserError):
            wiz.action_download_transfer_list()

        client = DachserRequest(self.carrier)

        mock_req.side_effect = requests.exceptions.Timeout("Read timeout")
        with self.assertRaises(UserError):
            client._request("GET", "routings")
        self.assertTrue(
            client._request("GET", "routings", raise_on_error=False)["_error"]
        )

        mock_req.side_effect = requests.exceptions.ConnectionError("Connection refused")
        with self.assertRaises(UserError):
            client._request("GET", "routings")
        self.assertTrue(
            client._request("GET", "routings", raise_on_error=False)["_error"]
        )
        mock_req.side_effect = None

        # HTTP 204 non-JSON, plain text 200, missing API key, Food division
        mock_req.return_value = self._mock_response(status_code=204, text=" ")
        self.assertEqual(
            client._request("DELETE", "transportorders/1")["_status_code"], 204
        )
        mock_req.return_value = self._mock_response(status_code=200, text="PLAIN_OK")
        self.assertEqual(client._request("GET", "routings")["raw"], "PLAIN_OK")

        self.carrier.write(
            {
                "dachser_api_key": False,
                "dachser_client_id": False,
                "dachser_division": "F",
            }
        )
        food_client = DachserRequest(self.carrier)
        self.assertEqual(food_client.division, "F")
        with self.assertRaises(UserError):
            food_client._get_api_key()
        self.carrier.dachser_api_key = "test-api-key-12345"
        self.assertNotIn("X-IBM-Client-Id", food_client._get_headers())
        self.carrier.write({"dachser_division": "T", "dachser_client_id": "ibm-001"})

        # Text splitting, UoM lb conversion, dimensionless package fallbacks
        self.assertEqual(client._split_text(""), [])
        self.assertEqual(
            client._split_text("X" * 45, max_len=30, max_items=2),
            ["X" * 30, "X" * 15],
        )
        self.assertEqual(client._convert_weight_to_kg(0.0), 0.0)
        self.assertEqual(client._convert_dimension_to_cm(0), 0)
        self.env["ir.config_parameter"].sudo().set_param("product.weight_in_lbs", "1")
        self.assertLess(client._convert_weight_to_kg(10.0), 10.0)
        self.env["ir.config_parameter"].sudo().set_param("product.weight_in_lbs", "0")

        for code, expected_l in (("EU", 120), ("EP", 80), ("IP", 120), ("KT", 60)):
            dimless_pkg = self.env["stock.package.type"].create(
                {
                    "name": f"Dimless {code}",
                    "package_carrier_type": "dachser",
                    "dachser_packaging_code": code,
                    "packaging_length": 0,
                    "width": 0,
                    "height": 0,
                }
            )
            l_cm, _w, _h, p_code, _ldm = client._get_package_dimensions_cm(dimless_pkg)
            self.assertEqual((l_cm, p_code), (expected_l, code))

        # Child contact & partner validation errors
        child_contact = self.env["res.partner"].create(
            {
                "name": "Dock Receiver",
                "parent_id": self.partner.id,
                "street": "Gate 5",
                "city": "Seville",
                "zip": "41001",
                "country_id": self.country_es.id,
            }
        )
        self.assertGreaterEqual(
            len(client._prepare_partner_data(child_contact)["names"]), 2
        )
        with self.assertRaises(UserError):
            client._validate_partner(self.env["res.partner"], picking=self.picking)
        incomplete = self.env["res.partner"].create(
            {"name": "No City", "country_id": self.country_es.id, "zip": "41001"}
        )
        with self.assertRaises(UserError):
            client._validate_partner(incomplete, picking=self.picking)

        # Routing and SSCC pool endpoints
        mock_req.return_value = self._mock_response(
            status_code=200, json_data={"printableRelation": "193-041-ES"}
        )
        routing = client.get_routing(self.partner, shipment_date="2026-11-17")
        self.assertEqual(routing["printableRelation"], "193-041-ES")

        mock_req.return_value = self._mock_response(
            status_code=200, json_data={"ssccs": ["00340336850590000099"]}
        )
        self.assertIn("ssccs", client.get_ssccs(count=5, use_prefix=True))
