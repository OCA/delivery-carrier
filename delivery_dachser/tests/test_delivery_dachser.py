# Copyright 2025 Tecnativa - Víctor Martínez
# Copyright 2026 Acysos S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from unittest.mock import MagicMock, patch

import requests

from odoo.exceptions import UserError, ValidationError
from odoo.tests import tagged
from odoo.tools import mute_logger

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

    def test_01_tariff_rule_all_calculation_modes_and_constraints(self):
        """Test all 5 tariff calculation modes, filters, surcharges, and
        weight/pallet constraints.
        """
        # 1. per_excess_kg (default rule)
        cost, breakdown = self.tariff_rule._compute_rule_cost(
            chargeable_weight_kg=100.0,
            packages_qty=1,
            tail_lift=True,
            has_notice=True,
        )
        # Base 20.0 + excess (50kg * 0.25 = 12.50) = 32.50
        # Fuel 5% of 32.50 = 1.625
        # Surcharges: tail_lift 12.0 + notice 3.5 = 15.50
        # Total = 32.50 + 1.625 + 15.50 = 49.625 -> 49.62
        self.assertAlmostEqual(cost, 49.62, places=1)
        self.assertIn("Spain Seville / Madrid Excess Kg", breakdown)

        # 2. fixed mode with min_charge
        self.tariff_rule.write(
            {"rate_type": "fixed", "base_price": 15.0, "min_charge": 25.0}
        )
        cost_fixed, _ = self.tariff_rule._compute_rule_cost(
            50.0, 1, tail_lift=False, has_notice=False
        )
        # Freight min_charge = 25.0 + 5% fuel (1.25) = 26.25
        self.assertAlmostEqual(cost_fixed, 26.25, places=2)

        # 3. per_kg mode
        self.tariff_rule.write(
            {
                "rate_type": "per_kg",
                "base_price": 10.0,
                "price_per_kg": 0.5,
                "min_charge": 0.0,
            }
        )
        cost_per_kg, _ = self.tariff_rule._compute_rule_cost(
            40.0, 1, tail_lift=False, has_notice=False
        )
        # (10 + 40*0.5 = 30) * 1.05 = 31.50
        self.assertAlmostEqual(cost_per_kg, 31.50, places=2)

        # 4. per_100kg mode
        self.tariff_rule.write(
            {"rate_type": "per_100kg", "base_price": 10.0, "price_per_kg": 15.0}
        )
        cost_100kg, _ = self.tariff_rule._compute_rule_cost(
            230.0, 1, tail_lift=False, has_notice=False
        )
        # 230 kg -> 3 fractions of 100kg -> (10 + 3*15 = 55) * 1.05 = 57.75
        self.assertAlmostEqual(cost_100kg, 57.75, places=2)

        # 5. per_pallet mode
        self.tariff_rule.write(
            {"rate_type": "per_pallet", "base_price": 5.0, "price_per_pallet": 40.0}
        )
        cost_pallet, _ = self.tariff_rule._compute_rule_cost(
            500.0, 2, tail_lift=False, has_notice=False
        )
        # (5 + 2*40 = 85) * 1.05 = 89.25
        self.assertAlmostEqual(cost_pallet, 89.25, places=2)

        # 6. Destination & weight/pallet matching and constraints
        self.assertTrue(
            self.tariff_rule._match_destination_and_shipment(self.partner, 100.0, 1)
        )
        with self.assertRaises(ValidationError):
            self.tariff_rule.write({"min_weight": 500.0, "max_weight": 100.0})
        with self.assertRaises(ValidationError):
            self.tariff_rule.write({"min_pallets": 5, "max_pallets": 2})

    def test_02_package_type_sync_and_volumetric_weight(self):
        """Test StockPackageType shipper_package_code sync, OCA
        number_of_packages sync, and volumetric/LDM chargeable weight.
        """
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

        # Sync between OCA delivery_package_number and dachser_packages_qty
        self.picking.number_of_packages = 3
        self.picking._onchange_number_of_packages_sync_dachser()
        self.assertEqual(self.picking.dachser_packages_qty, 3)

        self.picking.dachser_packages_qty = 4
        self.picking._onchange_dachser_packages_qty_sync_number()
        self.assertEqual(self.picking.number_of_packages, 4)

        # Volumetric: 2.0 m3 * 333 = 666 kg vs 100 kg gross vs 0.4 LDM * 1850 = 740 kg
        chargeable = self.carrier._dachser_compute_chargeable_weight(
            gross_weight_kg=100.0,
            volume_m3=2.0,
            ldm=0.4,
        )
        self.assertAlmostEqual(chargeable, 740.0, places=2)

    @patch(REQUEST_PATH)
    def test_03_rate_shipment_api_quotation_fallback_and_free_for_customer(
        self, mock_req
    ):
        """Test POST /rest/v2/quotations, fallback to local tariff table,
        ChooseDeliveryCarrier wizard, and free-for-customer internal cost
        preservation.
        """
        mock_req.return_value = self._mock_response(
            status_code=200,
            json_data={
                "id": "QUOT-2026-001",
                "totalAmount": {"amount": 78.50, "currency": "EUR"},
                "quotationDetails": [
                    {
                        "serviceType": "FRT",
                        "serviceTypeDescription": "Road Freight",
                        "serviceTypeAmount": {"amount": 72.00, "currency": "EUR"},
                    },
                    {
                        "serviceType": "BAF",
                        "serviceTypeDescription": "Diesel Surcharge",
                        "serviceTypeAmount": {"amount": 6.50, "currency": "EUR"},
                    },
                ],
                "remarks": ["Rate subject to current tariff terms"],
            },
        )
        res = self.carrier.dachser_rate_shipment(self.sale_order)
        self.assertTrue(res["success"])
        self.assertAlmostEqual(res["price"], 78.50, places=2)
        self.assertAlmostEqual(self.sale_order.dachser_estimated_cost, 78.50, places=2)
        self.assertEqual(self.sale_order.dachser_quotation_id, "QUOT-2026-001")
        self.assertIn("QUOT-2026-001", self.sale_order.dachser_rate_breakdown)

        # Test ChooseDeliveryCarrier wizard displays Dachser breakdown
        wiz = self.env["choose.delivery.carrier"].create(
            {
                "order_id": self.sale_order.id,
                "carrier_id": self.carrier.id,
            }
        )
        wiz.update_price()
        self.assertTrue(wiz.is_dachser_carrier)
        self.assertAlmostEqual(wiz.dachser_estimated_cost, 78.50, places=2)
        self.assertIn("QUOT-2026-001", wiz.dachser_rate_breakdown)

        # Test free_for_customer mode: customer pays 0.0 EUR, order keeps cost
        self.carrier.dachser_free_for_customer = True
        res_free = self.carrier.dachser_rate_shipment(self.sale_order)
        self.assertTrue(res_free["success"])
        self.assertEqual(res_free["price"], 0.0)
        self.assertAlmostEqual(self.sale_order.dachser_estimated_cost, 78.50, places=2)
        self.carrier.dachser_free_for_customer = False

        # Test API failure with automatic fallback to local tariff table
        mock_req.return_value = self._mock_response(
            status_code=422,
            json_data={
                "message": "No online tariff configured",
                "details": ["Contact branch"],
            },
        )
        res_fallback = self.carrier.dachser_rate_shipment(self.sale_order)
        self.assertTrue(res_fallback["success"])
        self.assertGreater(res_fallback["price"], 0.0)
        self.assertTrue(res_fallback["warning_message"])

    @patch(REQUEST_PATH)
    def test_04_send_shipping_transportorder_and_package_sscc(self, mock_req):
        """Test POST /rest/v2/transportorders/labelled with physical packages,
        SSCC assignment, OCA delivery_state, and PDF label.
        """
        pkg = self.env["stock.quant.package"].create(
            {
                "name": "PACK-DACHSER-001",
                "package_type_id": self.package_type_eu.id,
            }
        )
        self.picking.move_line_ids.write({"result_package_id": pkg.id})

        mock_req.return_value = self._mock_response(
            status_code=201,
            json_data={
                "id": 99001122,
                "state": "labelled",
                "ssccs": ["00340336850591178159"],
                "label": self.sample_pdf_b64,
                "messages": ["Order created in eLogistics"],
            },
        )
        self.picking.send_to_shipper()
        self.assertEqual(self.picking.dachser_transport_order_id, "99001122")
        self.assertEqual(self.picking.dachser_order_state, "labelled")
        self.assertEqual(self.picking.carrier_tracking_ref, "00340336850591178159")
        self.assertEqual(pkg.dachser_sscc, "00340336850591178159")
        self.assertEqual(self.picking.dachser_shipment_state, "registered")
        # Verify OCA delivery_state integration
        self.assertEqual(self.picking.delivery_state, "shipping_recorded_in_carrier")
        self.assertEqual(self.picking.tracking_state_history, "labelled")
        self.assertTrue(self.picking.dachser_tracking_url)

        # Verify PDF label attachment was created on the picking
        attachments = self.env["ir.attachment"].search(
            [
                ("res_model", "=", "stock.picking"),
                ("res_id", "=", self.picking.id),
                ("name", "ilike", "Dachser_Label_%"),
            ]
        )
        self.assertTrue(attachments)

    @patch(REQUEST_PATH)
    def test_05_send_shipping_label_only_and_test_fallback(self, mock_req):
        """Test automatic fallback in test mode to POST /rest/v2/labels when
        /transportorders returns 401.
        """
        unauth_resp = self._mock_response(
            status_code=401, text="Unauthorized for transportorders"
        )
        label_resp = self._mock_response(
            status_code=200,
            json_data={
                "ssccs": ["00340336850599999999"],
                "label": self.sample_pdf_b64,
                "relation": {
                    "printableRelation": "193-005-DE",
                    "relationCode": "005",
                },
            },
        )
        mock_req.side_effect = [unauth_resp, label_resp]

        ship_res = self.carrier.dachser_send_shipping(self.picking)
        self.assertEqual(ship_res[0]["tracking_number"], "00340336850599999999")
        self.assertEqual(self.picking.dachser_ldr_routing, "193-005-DE")

    @patch(REQUEST_PATH)
    def test_06_tms_send_reprint_label_and_routing(self, mock_req):
        """Test action_dachser_send_to_tms, action_dachser_get_label, and
        action_dachser_check_routing.
        """
        self.picking.write(
            {
                "dachser_transport_order_id": "99001122",
                "dachser_order_state": "labelled",
                "carrier_tracking_ref": "00340336850591178159",
            }
        )
        # 1. Confirm order to TMS
        mock_req.return_value = self._mock_response(
            status_code=200,
            json_data={
                "id": 99001122,
                "state": "sent",
                "ssccs": ["00340336850591178159"],
                "label": self.sample_pdf_b64,
            },
        )
        self.picking.action_dachser_send_to_tms()
        self.assertEqual(self.picking.dachser_order_state, "sent")
        self.assertEqual(self.picking.tracking_state_history, "sent")

        # 2. Reprint label
        mock_req.return_value = self._mock_response(
            status_code=200,
            json_data={
                "id": 99001122,
                "state": "sent",
                "ssccs": ["00340336850591178159"],
                "label": self.sample_pdf_b64,
            },
        )
        self.picking.action_dachser_get_label()

        # 3. Check LDR routing
        mock_req.return_value = self._mock_response(
            status_code=200,
            json_data={"printableRelation": "193-041-ES"},
        )
        self.picking.action_dachser_check_routing()
        self.assertEqual(self.picking.dachser_ldr_routing, "193-041-ES")

    @patch(REQUEST_PATH)
    def test_07_tracking_status_history_and_pod_download(self, mock_req):
        """Test live tracking status, OCA tracking_state_update, history
        events, tracking URL action, and POD PDF download.
        """
        self.picking.carrier_tracking_ref = "00340336850591178159"

        url_action = self.picking.action_open_dachser_tracking_url()
        self.assertEqual(url_action["type"], "ir.actions.act_url")
        self.assertIn("00340336850591178159", url_action["url"])

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
        mock_req.side_effect = [status_resp, history_resp]
        # Call OCA delivery_state's tracking_state_update() hook
        self.picking.tracking_state_update()
        self.assertEqual(self.picking.dachser_shipment_state, "delivered")
        self.assertEqual(self.picking.delivery_state, "customer_delivered")
        self.assertTrue(self.picking.date_delivered)
        self.assertEqual(self.picking.dachser_consignment_id, "81234567890")
        self.assertEqual(self.picking.dachser_pod_signor, "John Smith")
        self.assertIn("Picked up", self.picking.dachser_tracking_history)
        self.assertIn("Delivered", self.picking.dachser_tracking_history)

        # Download POD PDF and verify OCA pod_file & pod_filename are populated
        mock_req.side_effect = None
        mock_req.return_value = self._mock_response(
            status_code=200,
            json_data=[
                {
                    "consignmentId": "81234567890",
                    "archiveDate": "2026-11-06",
                    "podDocument": self.sample_pdf_b64,
                }
            ],
        )
        self.picking.action_dachser_get_pod()
        self.assertTrue(self.picking.dachser_pod_received)
        self.assertTrue(self.picking.pod_file)
        self.assertTrue(self.picking.pod_filename)

    @patch(REQUEST_PATH)
    def test_08_freight_costs_audit_and_cron(self, mock_req):
        """Test GET /rest/v2/freightcosts invoice cost auditing, cost
        deviation, and scheduled cron.
        """
        self.picking.write(
            {
                "state": "done",
                "date_done": "2026-11-06 09:00:00",
                "carrier_tracking_ref": "00340336850591178159",
                "dachser_estimated_cost": 50.0,
                "dachser_shipment_state": "delivered",
                "dachser_pod_received": True,
            }
        )
        mock_req.return_value = self._mock_response(
            status_code=200,
            json_data=[
                {
                    "consignmentNumber": "81234567890",
                    "invoiceNumber": "INV-DACHSER-2026-99",
                    "invoiceDate": "2026-11-06",
                    "chargableWeight": {"weight": 399.6, "unit": "KG"},
                    "totalAmount": {"amount": 55.25, "currency": "EUR"},
                    "costsDetails": [
                        {
                            "serviceType": "FRT",
                            "serviceTypeDescription": "Base Freight",
                            "serviceTypeAmount": {"amount": 55.25, "currency": "EUR"},
                        }
                    ],
                }
            ],
        )
        self.env["stock.picking"]._cron_dachser_update_shipments()
        self.assertAlmostEqual(self.picking.dachser_invoiced_cost, 55.25, places=2)
        self.assertAlmostEqual(self.picking.dachser_cost_difference, 5.25, places=2)
        self.assertEqual(self.picking.dachser_invoice_number, "INV-DACHSER-2026-99")

    @patch(REQUEST_PATH)
    def test_09_cancel_shipment_and_return_label(self, mock_req):
        """Test DELETE /rest/v2/transportorders/{id}, blocking cancel when
        sent, and return labels.
        """
        self.picking.write(
            {
                "dachser_transport_order_id": "99001122",
                "dachser_order_state": "sent",
                "carrier_tracking_ref": "00340336850591178159",
            }
        )
        # Cannot cancel an already sent order (check OCA-compatible error message)
        error_msg = (
            "It is not possible to cancel a shipment because it has already been sent."
        )
        with self.assertRaisesRegex(UserError, error_msg):
            self.picking.cancel_shipment()

        # Can cancel an imported/labelled order
        self.picking.dachser_order_state = "labelled"
        mock_req.return_value = self._mock_response(status_code=200, json_data={})
        self.picking.cancel_shipment()
        self.assertFalse(self.picking.carrier_tracking_ref)
        self.assertEqual(self.picking.dachser_order_state, "cancelled")
        self.assertEqual(self.picking.delivery_state, "canceled_shipment")

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
                ("name", "ilike", "Dachser_Return_%"),
            ]
        )
        self.assertTrue(ret_att)

    @mute_logger("odoo.addons.delivery_dachser.models.dachser_request")
    @patch(REQUEST_PATH)
    def test_10_transfer_list_wizard_and_api_error_handling(self, mock_req):
        """Test daily Transfer List PDF wizard and HTTP error codes
        (400, 429, 500, RequestException).
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

        # Test HTTP 429 Rate Limit error
        mock_req.return_value = self._mock_response(
            status_code=429, text="Too Many Requests"
        )
        with self.assertRaises(UserError):
            wiz.action_download_transfer_list()

        # Test network connection failure
        mock_req.side_effect = requests.exceptions.ConnectionError("Connection refused")
        with self.assertRaises(UserError):
            wiz.action_download_transfer_list()
