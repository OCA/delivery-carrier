# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64
import io
import json
from datetime import datetime, timedelta
from unittest import mock

import requests
from PIL import Image

from odoo.exceptions import UserError, ValidationError
from odoo.tests import Form, common
from odoo.tools import mute_logger

from ..models.ups_request import UpsRequest

_module_ns = "odoo.addons.delivery_ups_oca"
_provider_class = _module_ns + ".models.ups_request.UpsRequest"


class TestDeliveryUpsBase(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        product_shipping_cost = cls.env["product.product"].create(
            {
                "type": "service",
                "name": "Shipping costs",
                "standard_price": 10,
                "list_price": 100,
            }
        )
        cls.carrier = cls.env["delivery.carrier"].create(
            {
                "name": "UPS",
                "delivery_type": "ups",
                "product_id": product_shipping_cost.id,
                "price_method": "fixed",
                "ups_default_packaging_id": cls.env.ref(
                    "delivery_ups_oca.product_packaging_ups_02"
                ).id,
                "ups_shipper_number": "123456",
                "ups_service_code": "11",
                "ups_file_format": "GIF",
                "ups_tracking_state_update_sync": True,
                "ups_client_id": "test_client_id",
                "ups_client_secret": "test_client_secret",
                "ups_package_dimension_code": "IN",
                "ups_package_weight_code": "LBS",
                "ups_cash_on_delivery": False,
                "declared_value_percentage": 80,
            }
        )
        cls.company = cls.env.ref("base.main_company")
        cls.company.partner_id.write(
            {
                "phone": f"+{cls.company.country_id.phone_code}976123456",
                "vat": f"{cls.company.country_id.code}09915370R",
            }
        )
        cls.partner = cls.env["res.partner"].create(
            {
                "name": "Test partner",
                "country_id": cls.company.country_id.id,
                "phone": cls.company.partner_id.phone,
                "email": "test@odoo.com",
                "street": cls.company.partner_id.street,
                "city": cls.company.partner_id.city,
                "zip": cls.company.partner_id.zip,
                "state_id": cls.company.partner_id.state_id.id,
                "vat": cls.company.partner_id.vat,
            }
        )
        cls.product = cls.env["product.product"].create(
            {
                "name": "Test product",
                "type": "consu",
                "is_storable": True,
                "weight": 10,
            }
        )
        cls.sale = cls._create_sale_order(cls)
        # Create a simple 1x1 transparent GIF for testing
        buffer = io.BytesIO()
        img = Image.new("RGBA", (1, 1), (0, 0, 0, 0))
        img.save(buffer, format="GIF")
        cls.label = buffer.getvalue()

    def _create_sale_order(self):
        order_form = Form(self.env["sale.order"])
        order_form.partner_id = self.partner
        with order_form.order_line.new() as line_form:
            line_form.product_id = self.product
            line_form.product_uom_qty = 10
        sale = order_form.save()
        delivery_wizard = Form(
            self.env["choose.delivery.carrier"].with_context(
                **{"default_order_id": sale.id, "default_carrier_id": self.carrier.id}
            )
        ).save()
        delivery_wizard.button_confirm()
        sale.action_confirm()
        return sale

    def _patch_carrier_log_xml(self):
        """Helper to patch the log_xml method on carrier class"""
        return mock.patch.object(type(self.carrier), "log_xml")


class TestDeliveryUps(TestDeliveryUpsBase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.picking = cls.sale.picking_ids[0]
        cls.picking.company_id = cls.sale.company_id.id
        cls.picking.move_ids.quantity = 10

        # Create additional test data
        cls.package_type = cls.env["stock.package.type"].create(
            {
                "name": "Test UPS Package",
                "package_carrier_type": "ups",
                "shipper_package_code": "02",
                "packaging_length": 10,
                "width": 10,
                "height": 10,
            }
        )

    def test_order_ups_rate_shipment(self):
        """Test rate_shipment method - covers _rate_shipment and _process_reply"""
        # Create UPS request instance
        ups_request = UpsRequest(self.carrier)

        # Mock _process_reply to return a successful response
        with mock.patch.object(ups_request, "_process_reply") as mock_process_reply:
            # Mock the response structure. From v2409 on, RatedShipment is
            # always returned as an array.
            mock_process_reply.return_value = {
                "RateResponse": {
                    "RatedShipment": [
                        {
                            "TotalCharges": {
                                "MonetaryValue": "150.00",
                                "CurrencyCode": "USD",
                            }
                        }
                    ]
                }
            }

            # Mock _raise_for_status to do nothing
            with mock.patch.object(ups_request, "_raise_for_status"):
                # Call the actual _rate_shipment method
                result = ups_request._rate_shipment(self.sale)

                # Verify _process_reply was called with correct arguments
                mock_process_reply.assert_called_once()
                call_args = mock_process_reply.call_args

                # Check URL
                self.assertIn("/api/rating/v2409/Rate", call_args[1]["url"])

                # Check JSON data structure
                json_data = call_args[1]["json"]
                self.assertIn("RateRequest", json_data)
                self.assertIn("Shipment", json_data["RateRequest"])
                self.assertEqual(
                    json_data["RateRequest"]["Request"]["TransactionReference"][
                        "CustomerContext"
                    ],
                    self.sale.name,
                )

                # Verify result
                self.assertEqual(
                    result["RateResponse"]["RatedShipment"][0]["TotalCharges"][
                        "MonetaryValue"
                    ],
                    "150.00",
                )

    def test_order_ups_rate_shipment_currency_extra(self):
        usd = self.env.ref("base.USD")
        eur = self.env.ref("base.EUR")
        currency = self.env.ref("base.main_company").currency_id
        currency_extra = eur if currency == usd else usd
        self.sale.currency_id = currency_extra
        with mock.patch(
            _provider_class + "._rate_shipment",
            return_value={
                "RateResponse": {
                    "RatedShipment": [
                        {"TotalCharges": {"MonetaryValue": 1, "CurrencyCode": "USD"}}
                    ]
                }
            },
        ):
            res = self.carrier.ups_rate_shipment(self.sale)
            self.assertGreater(res["price"], 0)
            self.assertTrue(res["success"])

    def test_order_ups_rate_shipment_single_object(self):
        """Pre-v2409 responses with a bare RatedShipment object still work."""
        with mock.patch(
            _provider_class + "._rate_shipment",
            return_value={
                "RateResponse": {
                    "RatedShipment": {
                        "TotalCharges": {"MonetaryValue": 12, "CurrencyCode": "USD"}
                    }
                }
            },
        ):
            res = self.carrier.ups_rate_shipment(self.sale)
            self.assertTrue(res["success"])
            self.assertGreater(res["price"], 0)

    def test_order_ups_rate_shipment_no_rate(self):
        """An empty RatedShipment container is reported as a failure."""
        with mock.patch(
            _provider_class + "._rate_shipment",
            return_value={"RateResponse": {}},
        ):
            res = self.carrier.ups_rate_shipment(self.sale)
        self.assertFalse(res["success"])
        self.assertEqual(res["price"], 0.0)
        self.assertIn("no rate", res["error_message"])

    def test_ups_rate_shipment_unavailable_service(self):
        """A UserError during rating is swallowed so the method can be hidden."""
        with mock.patch(
            _provider_class + "._rate_shipment",
            side_effect=UserError("111217: service unavailable"),
        ):
            res = self.carrier.ups_rate_shipment(self.sale)
        self.assertFalse(res["success"])
        self.assertEqual(res["price"], 0.0)
        self.assertIn("111217", res["error_message"])
        self.assertFalse(res["warning_message"])

    def test_delivery_carrier_ups_integration(self):
        self.picking.action_confirm()
        self.picking.action_assign()
        # Create a simple PDF-like bytes object for testing
        label = b"%PDF-1.4\n%EOF"
        with mock.patch(
            _provider_class + "._send_shipping",
            return_value={
                "price": {"CurrencyCode": "USD", "MonetaryValue": "0.0"},
                "ShipmentIdentificationNumber": "123456",
                "labels": [
                    {
                        "tracking_ref": "123456",
                        "format_code": "png",
                        "datas": base64.b64encode(label),
                    }
                ],
            },
        ):
            self.picking.send_to_shipper()
            self.assertEqual(self.picking.message_attachment_count, 1)
            self.assertTrue(self.picking.carrier_tracking_ref)
            self.assertFalse(self.picking.tracking_state_history)
            self.assertEqual(
                self.picking.delivery_state, "shipping_recorded_in_carrier"
            )
            if self.picking.carrier_id.ups_tracking_state_update_sync:
                with mock.patch(
                    _provider_class + ".tracking_state_update",
                    return_value={
                        "delivery_state": "in_transit",
                        "tracking_state_history": "history",
                        "tracking_state": "[300] In Transit",
                    },
                ):
                    self.picking.tracking_state_update()
                    self.assertEqual(self.picking.delivery_state, "in_transit")
                    self.assertTrue(self.picking.tracking_state_history)
            # Cancel UPS Picking
            with mock.patch(
                _provider_class + ".cancel_shipment",
                return_value=True,
            ):
                self.picking.cancel_shipment()
                self.assertFalse(self.picking.carrier_tracking_ref)
                self.assertEqual(self.picking.delivery_state, "canceled_shipment")

    def test_ups_create_shipping(self):
        with mock.patch(
            _provider_class + "._send_shipping",
            return_value={
                "price": {"CurrencyCode": "USD", "MonetaryValue": "10.0"},
                "ShipmentIdentificationNumber": "123456",
                "labels": [
                    {
                        "tracking_ref": "123456",
                        "format_code": "GIF",
                        "datas": base64.b64encode(self.label),
                    }
                ],
            },
        ):
            result = self.carrier.ups_create_shipping(self.picking)
            self.assertEqual(result["tracking_number"], "123456")
            self.assertEqual(result["exact_price"], 10.0)
            self.assertEqual(self.picking.carrier_tracking_ref, "123456")
            # Picking status
            ups_request = UpsRequest(self.carrier)
            with mock.patch.object(ups_request, "_process_reply", return_value=result):
                with mock.patch.object(ups_request, "_raise_for_status"):
                    # Call _send_shipping
                    result = ups_request._send_shipping(self.picking)
                    # # Verify result
                    self.assertEqual(result["ShipmentIdentificationNumber"], "123456")
                    self.assertEqual(result["price"]["CurrencyCode"], "USD")
                    self.assertEqual(result["price"]["MonetaryValue"], "10.0")
                    self.assertEqual(len(result["labels"]), 1)
                    self.assertEqual(result["labels"][0]["tracking_ref"], "123456")
                    self.assertEqual(result["labels"][0]["format_code"], "GIF")

    def test_ups_send_shipping(self):
        # Mock the dependencies
        mock_response = {
            "ShipmentResponse": {
                "ShipmentResults": {
                    "PackageResults": {
                        "TrackingNumber": "TRACK123456",
                        "ShippingLabel": {
                            "ImageFormat": {"Code": "PDF"},
                            "GraphicImage": "base64_encoded_pdf_data",
                        },
                    },
                    "ShipmentCharges": {"TotalCharges": "45.99"},
                    "ShipmentIdentificationNumber": "SHIP123456789",
                }
            }
        }
        self.picking.number_of_packages = 1
        ups_request = UpsRequest(self.carrier)
        with (
            mock.patch.object(
                ups_request, "_process_reply", return_value=mock_response
            ) as mock_process_reply,
            mock.patch.object(ups_request, "_raise_for_status"),
        ):
            result = ups_request._send_shipping(self.picking)
            self.assertIn(
                "/api/shipments/v2409/ship", mock_process_reply.call_args[1]["url"]
            )
            request_json = mock_process_reply.call_args[1]["json"]
            self.assertEqual(
                request_json["ShipmentRequest"]["Request"]["RequestOption"],
                "nonvalidate",
            )
            self.assertEqual(result["price"], "45.99")
            self.assertEqual(result["ShipmentIdentificationNumber"], "SHIP123456789")
            self.assertEqual(len(result["labels"]), 1)
            self.assertEqual(result["labels"][0]["tracking_ref"], "TRACK123456")
            self.assertEqual(result["labels"][0]["format_code"], "PDF")
            self.assertEqual(result["labels"][0]["datas"], "base64_encoded_pdf_data")

    def test_ups_send_shipping_multi_pack(self):
        # Mock the dependencies
        mock_response = {
            "ShipmentResponse": {
                "ShipmentResults": {
                    "PackageResults": [
                        {
                            "TrackingNumber": "TRACK123456",
                            "ShippingLabel": {
                                "ImageFormat": {"Code": "PDF"},
                                "GraphicImage": "base64_encoded_pdf_data",
                            },
                        },
                        {
                            "TrackingNumber": "TRACK123457",
                            "ShippingLabel": {
                                "ImageFormat": {"Code": "PDF"},
                                "GraphicImage": "base64_encoded_pdf_data",
                            },
                        },
                    ],
                    "ShipmentCharges": {"TotalCharges": "50.99"},
                    "ShipmentIdentificationNumber": "SHIP22222",
                }
            }
        }
        self.picking.number_of_packages = 2
        ups_request = UpsRequest(self.carrier)
        with (
            mock.patch.object(
                ups_request, "_process_reply", return_value=mock_response
            ),
            mock.patch.object(ups_request, "_raise_for_status"),
        ):
            result = ups_request._send_shipping(self.picking)
            self.assertEqual(result["price"], "50.99")
            self.assertEqual(result["ShipmentIdentificationNumber"], "SHIP22222")
            self.assertEqual(len(result["labels"]), 2)
            self.assertEqual(result["labels"][0]["tracking_ref"], "TRACK123456")

    def test_ups_send_shipping_multiple_pickings(self):
        # Create a second picking
        picking2 = self.picking.copy()
        picking2.move_ids.quantity = 5
        with mock.patch(
            _provider_class + "._send_shipping",
            side_effect=[
                {
                    "price": {"CurrencyCode": "USD", "MonetaryValue": "10.0"},
                    "ShipmentIdentificationNumber": "123456",
                    "labels": [
                        {
                            "tracking_ref": "123456",
                            "format_code": "GIF",
                            "datas": base64.b64encode(self.label),
                        }
                    ],
                },
                {
                    "price": {"CurrencyCode": "USD", "MonetaryValue": "15.0"},
                    "ShipmentIdentificationNumber": "789012",
                    "labels": [
                        {
                            "tracking_ref": "789012",
                            "format_code": "GIF",
                            "datas": base64.b64encode(self.label),
                        }
                    ],
                },
            ],
        ):
            results = self.carrier.ups_send_shipping(self.picking + picking2)
            self.assertEqual(len(results), 2)
            self.assertEqual(results[0]["tracking_number"], "123456")
            self.assertEqual(results[1]["tracking_number"], "789012")

    def test_ups_get_label(self):
        ups_request = UpsRequest(self.carrier)
        carrier_tracking_ref = "1Z12345E0291980793"
        mock_label_data = b"%PDF-1.4\nTest PDF Content\n%%EOF"
        mock_response = {
            "LabelRecoveryResponse": {
                "LabelResults": {
                    "TrackingNumber": "1Z12345E0291980793",
                    "LabelImage": {
                        "LabelImageFormat": {"Code": "PDF"},
                        "GraphicImage": base64.b64encode(mock_label_data).decode(
                            "ascii"
                        ),
                    },
                }
            }
        }
        with mock.patch.object(
            ups_request, "_process_reply", return_value=mock_response
        ) as mock_process_reply:
            with mock.patch.object(
                ups_request,
                "_prepare_shipping_label",
                return_value={"TrackingNumber": carrier_tracking_ref},
            ):
                # Call the method
                labels = ups_request.shipping_label(carrier_tracking_ref)
                # Verify the result
                self.assertIn(
                    "/api/labels/v2603/recovery",
                    mock_process_reply.call_args[1]["url"],
                )
                self.assertEqual(len(labels), 1)
                self.assertEqual(labels[0]["tracking_ref"], "1Z12345E0291980793")
                self.assertEqual(labels[0]["format_code"], "PDF")
                self.assertEqual(
                    labels[0]["datas"],
                    base64.b64encode(mock_label_data).decode("ascii"),
                )

    def test_ups_prepare_shipping_label_request_container(self):
        """The label recovery request carries the documented Request container."""
        ups_request = UpsRequest(self.carrier)
        request = ups_request._prepare_shipping_label("1Z12345E0291980793")
        recovery_request = request["LabelRecoveryRequest"]
        self.assertEqual(
            recovery_request["Request"]["TransactionReference"]["CustomerContext"],
            "1Z12345E0291980793",
        )
        self.assertEqual(recovery_request["TrackingNumber"], "1Z12345E0291980793")

    def test_ups_get_label_pdf(self):
        self.carrier.ups_file_format = "PDF"
        ups_request = UpsRequest(self.carrier)
        carrier_tracking_ref = "1Z12345E0291980793"
        mock_label_data = b"%PDF-1.4\nTest PDF Content\n%%EOF"
        mock_response = {
            "LabelRecoveryResponse": {
                "LabelResults": {
                    "TrackingNumber": "1Z12345E0291980793",
                    "LabelImage": {
                        "LabelImageFormat": {"Code": "PDF"},
                        "GraphicImage": base64.b64encode(mock_label_data).decode(
                            "ascii"
                        ),
                    },
                }
            }
        }
        with mock.patch.object(
            ups_request, "_process_reply", return_value=mock_response
        ):
            with mock.patch.object(
                ups_request,
                "_prepare_shipping_label",
                return_value={"TrackingNumber": carrier_tracking_ref},
            ):
                # Call the method
                labels = ups_request.shipping_label(carrier_tracking_ref)
                # Verify the result
                self.assertEqual(len(labels), 1)
                self.assertEqual(labels[0]["tracking_ref"], "1Z12345E0291980793")
                self.assertEqual(labels[0]["format_code"], "PDF")
                self.assertEqual(
                    labels[0]["datas"],
                    base64.b64encode(mock_label_data).decode("ascii"),
                )

    def test_shipping_label_multiple_list(self):
        ups_request = UpsRequest(self.carrier)
        carrier_tracking_ref = "1Z12345E0291980793"
        mock_label1_data = b"%PDF-1.4\nTest PDF Content\n%%EOF"
        mock_label2_data = b"%PDF-1.4\nTest PDF Content\n%%EOF"
        mock_response = {
            "LabelRecoveryResponse": {
                "LabelResults": [
                    {
                        "TrackingNumber": "1Z12345E0291980793",
                        "LabelImage": {
                            "LabelImageFormat": {"Code": "GIF"},
                            "GraphicImage": base64.b64encode(mock_label1_data).decode(
                                "ascii"
                            ),
                        },
                    },
                    {
                        "TrackingNumber": "1Z12345E0291980794",
                        "LabelImage": {
                            "LabelImageFormat": {"Code": "GIF"},
                            "GraphicImage": base64.b64encode(mock_label2_data).decode(
                                "ascii"
                            ),
                        },
                    },
                ]
            }
        }
        with mock.patch.object(
            ups_request, "_process_reply", return_value=mock_response
        ):
            with mock.patch.object(
                ups_request,
                "_prepare_shipping_label",
                return_value={"TrackingNumber": carrier_tracking_ref},
            ):
                # Call the method
                labels = ups_request.shipping_label(carrier_tracking_ref)
                # Verify the result
                self.assertEqual(len(labels), 2)
                # Verify first label
                self.assertEqual(labels[0]["tracking_ref"], "1Z12345E0291980793")
                self.assertEqual(labels[0]["format_code"], "GIF")
                self.assertEqual(
                    labels[0]["datas"],
                    base64.b64encode(mock_label1_data).decode("ascii"),
                )
                # Verify second label
                self.assertEqual(labels[1]["tracking_ref"], "1Z12345E0291980794")
                self.assertEqual(labels[1]["format_code"], "GIF")
                self.assertEqual(
                    labels[1]["datas"],
                    base64.b64encode(mock_label2_data).decode("ascii"),
                )

    def test_ups_get_label_no_tracking_ref(self):
        result = self.carrier.ups_get_label(False)
        self.assertFalse(result)

    def test_ups_get_tracking_link(self):
        self.picking.carrier_tracking_ref = "123456"
        tracking_link = self.carrier.ups_get_tracking_link(self.picking)
        expected_link = "https://ups.com/WebTracking/track?trackingNumber=123456"
        self.assertEqual(tracking_link, expected_link)

    def test_ups_cancel_shipment(self):
        """Test successful shipment cancellation"""
        ups_request = UpsRequest(self.carrier)
        self.picking.carrier_tracking_ref = "123456"
        # Mock successful response
        mock_response = {
            "VoidShipmentResponse": {
                "Response": {"ResponseStatus": {"Code": "1", "Description": "Success"}}
            }
        }
        with mock.patch.object(
            ups_request, "_process_reply", return_value=mock_response
        ) as mock_process_reply:
            with mock.patch.object(ups_request, "_raise_for_status", return_value=True):
                result = ups_request.cancel_shipment(self.picking)
                self.assertTrue(result)
                self.assertIn(
                    "/api/shipments/v2409/void/cancel/123456",
                    mock_process_reply.call_args[1]["url"],
                )

    def test_ups_tracking_state_update(self):
        self.picking.carrier_tracking_ref = "123456"
        with mock.patch(
            _provider_class + ".tracking_state_update",
            return_value={
                "delivery_state": "in_transit",
                "tracking_state_history": "Test history",
                "tracking_state": "[300] In Transit",
            },
        ):
            self.carrier.ups_tracking_state_update(self.picking)
            self.assertEqual(self.picking.delivery_state, "in_transit")
            self.assertEqual(self.picking.tracking_state_history, "Test history")

    def test_ups_tracking_state_update_no_sync(self):
        self.carrier.ups_tracking_state_update_sync = False
        self.picking.carrier_tracking_ref = "123456"
        self.carrier.ups_tracking_state_update(self.picking)
        # Should do nothing when sync is disabled

    def test_ups_tracking_state_update_no_tracking_ref(self):
        self.picking.carrier_tracking_ref = False
        self.carrier.ups_tracking_state_update(self.picking)
        # Should do nothing when no tracking reference

    def test_ups_get_new_token_no_credentials(self):
        """Test _get_new_token raises UserError when no client credentials"""
        # Set no client credentials on carrier
        self.carrier.ups_client_id = False
        self.carrier.ups_client_secret = False
        # Create UpsRequest instance
        ups_request = UpsRequest(self.carrier)
        # The _get_new_token method should raise UserError when no credentials
        with self.assertRaises(UserError) as context:
            ups_request._get_new_token()
        # Get the exception message
        error_msg = str(context.exception)
        self.assertIn("Client ID", error_msg)
        self.assertIn("Client Secret", error_msg)
        self.assertIn("must be set", error_msg)

    def test_ups_update_token(self):
        # Test the actual token update with proper mock
        with mock.patch(
            _provider_class + "._get_new_token",
            return_value=None,
        ):
            # Test with client_id and client_secret
            self.carrier.ups_client_id = "test_id"
            self.carrier.ups_client_secret = "test_secret"
            self.carrier.ups_update_token()

            # Test without client credentials
            self.carrier.ups_client_id = False

    def test_ups_update_token_expired(self):
        # Test token update when token is expired
        self.carrier.ups_token_expiration_date = datetime.now() - timedelta(days=1)
        self.carrier.ups_client_id = "test_id"
        self.carrier.ups_client_secret = "test_secret"

        with mock.patch(
            _provider_class + "._get_new_token",
            return_value=None,
        ):
            self.carrier.ups_update_token()
            # Should call _get_new_token when token is expired

    def test_picking_ups_get_label_wrong_carrier(self):
        self.picking.carrier_id.delivery_type = "fixed"
        self.picking.carrier_tracking_ref = "123456"
        result = self.picking.ups_get_label()
        self.assertIsNone(result)

    def test_picking_ups_get_label_no_tracking(self):
        self.picking.carrier_tracking_ref = False
        result = self.picking.ups_get_label()
        self.assertIsNone(result)

    def test_ups_rate_shipment_with_packages(self):
        # Test with packages from picking
        self.carrier.ups_use_packages_from_picking = True
        package = self.env["stock.quant.package"].create(
            {
                "name": "Test Package",
                "shipping_weight": 5,
            }
        )
        self.picking.move_ids.move_line_ids.result_package_id = package.id

        with mock.patch(
            _provider_class + "._rate_shipment",
            return_value={
                "RateResponse": {
                    "RatedShipment": [
                        {"TotalCharges": {"MonetaryValue": 1, "CurrencyCode": "USD"}}
                    ]
                }
            },
        ):
            res = self.carrier.ups_rate_shipment(self.sale)
            self.assertGreater(res["price"], 0)
            self.assertTrue(res["success"])

    def test_ups_label_attachment_preparation(self):
        # Test label attachment preparation
        picking = self.picking
        values = {
            "name": "test_label.GIF",
            "datas": base64.b64encode(b"test"),
        }
        attachment_data = self.carrier._prepare_ups_label_attachment(picking, values)
        self.assertEqual(attachment_data["name"], "test_label.GIF")
        self.assertEqual(attachment_data["res_model"], picking._name)
        self.assertEqual(attachment_data["res_id"], picking.id)

    def test_ups_create_label_multiple_labels(self):
        # Test creating multiple labels
        labels = [
            {
                "tracking_ref": "123456",
                "format_code": "GIF",
                "datas": base64.b64encode(self.label),
            },
            {
                "tracking_ref": "789012",
                "format_code": "ZPL",
                "datas": base64.b64encode(self.label),
            },
        ]
        attachments = self.carrier._create_ups_label(self.picking, labels)
        self.assertEqual(len(attachments), 2)
        self.assertEqual(attachments[0].name, "123456-GIF.gif")
        self.assertEqual(attachments[1].name, "789012-ZPL.zpl")

    def test_ups_process_reply_basic_success_with_helper(self):
        """Test using helper method for patching"""
        # Set up a valid token
        future_date = datetime.now() + timedelta(hours=1)
        self.carrier.ups_token = "valid_token_123"
        self.carrier.ups_token_expiration_date = future_date

        ups_request = UpsRequest(self.carrier)

        # Mock the HTTP response
        mock_response = mock.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True, "data": "test_data"}

        with mock.patch.object(
            ups_request, "_send_request", return_value=mock_response
        ):
            # Use the helper method
            with self._patch_carrier_log_xml() as mock_log:
                result = ups_request._process_reply(
                    url="https://api.test.com/endpoint",
                    json={"key": "value"},
                    method="post",
                    headers_extra={"Content-Type": "application/json"},
                )
                # Verify result
                self.assertEqual(result, {"success": True, "data": "test_data"})
                self.assertEqual(mock_log.call_count, 2)

    def test_send_request_passes_timeout(self):
        """The timeout must be forwarded to the underlying requests call."""
        ups_request = UpsRequest(self.carrier)
        mock_response = mock.Mock()
        with mock.patch(
            "odoo.addons.delivery_ups_oca.models.ups_request.requests"
        ) as mock_requests:
            mock_requests.post.return_value = mock_response
            result = ups_request._send_request(
                "https://api.test.com/endpoint",
                json={"key": "value"},
                timeout=10,
            )
        self.assertEqual(result, mock_response)
        mock_requests.post.assert_called_once()
        self.assertEqual(mock_requests.post.call_args.kwargs["timeout"], 10)

    def test_ups_transaction_headers(self):
        """UPS identifies callers through the transId/transactionSrc headers."""
        ups_request = UpsRequest(self.carrier)
        headers = ups_request._transaction_headers()
        # UPS limits transId to 32 characters
        self.assertEqual(len(headers["transId"]), 32)
        self.assertNotEqual(
            headers["transId"], ups_request._transaction_headers()["transId"]
        )
        self.assertEqual(headers["transactionSrc"], f"Odoo ({self.carrier.name})")

    def test_ups_get_new_token_success(self):
        self.carrier.ups_client_id = "test_id"
        self.carrier.ups_client_secret = "test_secret"

        ups_request = UpsRequest(self.carrier)

        mock_response = mock.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "abc123",
            "expires_in": 3600,
        }

        with mock.patch.object(
            ups_request, "_send_request", return_value=mock_response
        ):
            before = datetime.now()
            ups_request._get_new_token()

        self.assertEqual(ups_request.token, "abc123")
        self.assertEqual(self.carrier.ups_token, "abc123")
        self.assertGreater(self.carrier.ups_token_expiration_date, before)

    def test_ups_process_reply_401_retry(self):
        future_date = datetime.now() + timedelta(hours=1)
        self.carrier.ups_token = "valid_token_123"
        self.carrier.ups_token_expiration_date = future_date

        ups_request = UpsRequest(self.carrier)

        unauthorized_response = mock.Mock()
        unauthorized_response.status_code = 401

        success_response = mock.Mock()
        success_response.status_code = 200
        success_response.json.return_value = {"success": True, "data": "test_data"}

        with (
            mock.patch.object(
                ups_request,
                "_send_request",
                side_effect=[unauthorized_response, success_response],
            ) as mock_send_request,
            mock.patch.object(ups_request, "_get_new_token") as mock_get_new_token,
            self._patch_carrier_log_xml(),
        ):
            result = ups_request._process_reply(
                url="https://api.test.com/endpoint",
                json={"key": "value"},
                method="post",
            )

        self.assertEqual(result, {"success": True, "data": "test_data"})
        self.assertEqual(mock_send_request.call_count, 2)
        mock_get_new_token.assert_called_once()

    def test_ups_prepare_create_shipping_with_packages(self):
        """Test _prepare_create_shipping with packages from picking"""
        # Enable use packages from picking
        self.carrier.ups_use_packages_from_picking = True

        ups_request = UpsRequest(self.carrier)

        # Create test packages
        package1 = self.env["stock.quant.package"].create(
            {
                "name": "Package 1",
                "shipping_weight": 5.0,
            }
        )
        # Create package type
        package_type1 = self.env["stock.package.type"].create(
            {
                "name": "Test Package Type - 001",
                "shipper_package_code": "001",
                "packaging_length": 10.0,
                "width": 8.0,
                "height": 6.0,
            }
        )
        package1.package_type_id = package_type1
        package2 = self.env["stock.quant.package"].create(
            {
                "name": "Package 2",
                "shipping_weight": 3.0,
            }
        )
        # Create package type
        package_type2 = self.env["stock.package.type"].create(
            {
                "name": "Test Package Type - 002",
                "shipper_package_code": "002",
                "packaging_length": 10.0,
                "width": 8.0,
                "height": 6.0,
            }
        )
        package2.package_type_id = package_type2

        # Set packages on move lines.
        move = self.picking.move_ids
        move.move_line_ids.unlink()
        self.env["stock.move.line"].create(
            [
                {
                    "move_id": move.id,
                    "picking_id": self.picking.id,
                    "product_id": self.product.id,
                    "product_uom_id": move.product_uom.id,
                    "result_package_id": package1.id,
                    "quantity": 2,
                },
                {
                    "move_id": move.id,
                    "picking_id": self.picking.id,
                    "product_id": self.product.id,
                    "product_uom_id": move.product_uom.id,
                    "result_package_id": package2.id,
                    "quantity": 3,
                },
            ]
        )

        # Set picking data
        self.picking.name = "TEST0001"
        self.picking.shipping_weight = 8.0  # 5 + 3
        self.picking.number_of_packages = 2

        # Prepare shipping data
        result = ups_request._prepare_create_shipping(self.picking)
        packages = result["ShipmentRequest"]["Shipment"]["Package"]
        self.assertEqual(len(packages), 2)
        # Verify package descriptions (order is not guaranteed)
        descriptions = {package["Description"] for package in packages}
        self.assertEqual(descriptions, {package_type1.name, package_type2.name})
        # Verify service code
        self.assertEqual(result["ShipmentRequest"]["Shipment"]["Service"]["Code"], "11")
        # Verify label specification
        self.assertIn("LabelSpecification", result["ShipmentRequest"])
        self.assertEqual(
            result["ShipmentRequest"]["LabelSpecification"]["LabelImageFormat"]["Code"],
            "GIF",
        )

    def test_ups_prepare_create_shipping_address_validation(self):
        """RequestOption follows the carrier's address validation setting"""
        self.assertEqual(self.carrier.ups_address_validation, "nonvalidate")
        self.carrier.ups_address_validation = "validate"
        self.picking.name = "TEST0003"
        self.picking.number_of_packages = 1
        result = UpsRequest(self.carrier)._prepare_create_shipping(self.picking)
        self.assertEqual(
            result["ShipmentRequest"]["Request"]["RequestOption"], "validate"
        )

    def test_ups_prepare_create_shipping_without_packages(self):
        """Test _prepare_create_shipping without packages (uses default packaging)"""
        self.carrier.ups_use_packages_from_picking = False

        ups_request = UpsRequest(self.carrier)

        # Set picking data
        self.picking.name = "TEST0002"
        self.picking.shipping_weight = 30.0
        self.picking.number_of_packages = 3

        # # Create default packaging
        default_packaging = self.env["stock.package.type"].create(
            {
                "name": "UPS Box",
                "package_carrier_type": "ups",
                "shipper_package_code": "02",
                "packaging_length": 12.0,
                "width": 10.0,
                "height": 8.0,
            }
        )
        self.carrier.ups_default_packaging_id = default_packaging

        # Prepare shipping data
        result = ups_request._prepare_create_shipping(self.picking)

        # Verify the Request container required by the Ship API
        request = result["ShipmentRequest"]["Request"]
        self.assertEqual(request["RequestOption"], "nonvalidate")
        self.assertEqual(request["TransactionReference"]["CustomerContext"], "TEST0002")

        # Verify structure
        packages = result["ShipmentRequest"]["Shipment"]["Package"]
        self.assertEqual(len(packages), 3)  # Should create 3 packages

        # Each package should have weight = 30/3 = 10.0
        for i, package in enumerate(packages):
            self.assertEqual(package["Description"], f"TEST0002 ({i+1})")
            self.assertEqual(package["NumOfPieces"], "1")
            self.assertEqual(package["PackageWeight"]["Weight"], "10.0")  # 30/3 = 10
            self.assertEqual(package["Packaging"]["Code"], "02")

    def test_ups_prepare_create_shipping_zero_packages(self):
        """Send a single package when number_of_packages is 0."""
        self.carrier.ups_use_packages_from_picking = False
        ups_request = UpsRequest(self.carrier)
        self.picking.name = "TEST0007"
        self.picking.shipping_weight = 12.0
        self.picking.number_of_packages = 0
        result = ups_request._prepare_create_shipping(self.picking)
        shipment = result["ShipmentRequest"]["Shipment"]
        self.assertEqual(len(shipment["Package"]), 1)
        self.assertEqual(shipment["Package"][0]["PackageWeight"]["Weight"], "12.0")
        self.assertEqual(shipment["Service"]["Code"], "11")

    def test_ups_prepare_create_shipping_with_cash_on_delivery(self):
        """Test _prepare_create_shipping with cash on delivery"""
        # Enable cash on delivery
        self.carrier.ups_cash_on_delivery = True
        self.carrier.ups_cod_funds_code = "1"  # Cash
        ups_request = UpsRequest(self.carrier)
        # Set sale order amount
        self.sale.amount_total = 11.5
        self.sale.currency_id = self.env.ref("base.USD")
        # Ensure picking is linked to sale order
        self.picking.sale_id = self.sale
        # Set picking data
        self.picking.name = "TEST0006"
        self.picking.shipping_weight = 8.0
        self.picking.number_of_packages = 2
        # Prepare shipping data
        result = ups_request._prepare_create_shipping(self.picking)
        # Verify cash on delivery data is included
        shipment = result["ShipmentRequest"]["Shipment"]
        self.assertIn("ShipmentServiceOptions", shipment)
        cod_data = shipment["ShipmentServiceOptions"]["COD"]
        self.assertEqual(cod_data["CODFundsCode"], "1")
        self.assertEqual(cod_data["CODAmount"]["CurrencyCode"], "USD")
        self.assertEqual(cod_data["CODAmount"]["MonetaryValue"], "11.5")
        # Verify other shipment details
        self.assertEqual(shipment["Description"], "TEST0006")
        self.assertEqual(shipment["Service"]["Code"], "11")
        self.assertEqual(len(shipment["Package"]), 2)

    def check_declared_value_packages(self, carrier, picking):
        ups_request = UpsRequest(carrier)
        vals = ups_request._prepare_create_shipping(picking)
        packages = vals["ShipmentRequest"]["Shipment"]["Package"]
        for package in packages:
            self.assertIn("PackageServiceOptions", package)
            self.assertIn("DeclaredValue", package["PackageServiceOptions"])
            declared_value = package["PackageServiceOptions"]["DeclaredValue"]
            self.assertEqual(declared_value["MonetaryValue"], "8.0")
            self.assertEqual(
                declared_value["CurrencyCode"],
                picking.declared_value_currency_id.name,
            )

    def test_declared_value_with_packages(self):
        """Test that declared value is added when packages exist"""
        pack_action = self.picking.action_put_in_pack()
        pack_action_ctx = pack_action["context"]
        pack_wiz = (
            self.env["choose.delivery.package"]
            .with_context(**pack_action_ctx)
            .create(
                {"delivery_package_type_id": self.carrier.ups_default_packaging_id.id}
            )
        )
        pack_wiz.action_put_in_pack()

        self.carrier.write({"ups_use_packages_from_picking": True})
        self.picking.declared_value = 8.0
        self.check_declared_value_packages(self.carrier, self.picking)

    def test_declared_value_without_packages(self):
        """Test declared value when no packages are defined"""
        self.picking.move_line_ids.write({"result_package_id": False})
        self.carrier.write({"ups_use_packages_from_picking": False})
        self.picking.number_of_packages = 1
        self.picking.declared_value = 8.0
        self.check_declared_value_packages(self.carrier, self.picking)

    def test_declared_value_not_added_when_zero(self):
        """No DeclaredValue is emitted when the declared value is 0."""
        self.picking.move_line_ids.write({"result_package_id": False})
        self.carrier.write({"ups_use_packages_from_picking": False})
        self.picking.number_of_packages = 1
        self.picking.declared_value = 0.0
        ups_request = UpsRequest(self.carrier)
        vals = ups_request._prepare_create_shipping(self.picking)
        packages = vals["ShipmentRequest"]["Shipment"]["Package"]
        self.assertTrue(packages)
        for package in packages:
            self.assertNotIn("PackageServiceOptions", package)

    def test_declared_value_percentage_constraint(self):
        """The declared value percentage must be within 0..100."""
        with self.assertRaises(ValidationError):
            self.carrier.declared_value_percentage = -1.0
        with self.assertRaises(ValidationError):
            self.carrier.declared_value_percentage = 101.0

    def test_declared_value_computed_from_sale_order(self):
        """The declared value sums the picked items' taxed sale order prices."""
        self.carrier.declared_value_percentage = 80.0
        sale_line = self.picking.move_ids.sale_line_id
        unit_price = sale_line.price_total / sale_line.product_uom_qty
        expected_base = unit_price * self.picking.move_ids.quantity
        self.picking.invalidate_recordset(["declared_value"])
        self.assertAlmostEqual(self.picking.declared_value, expected_base * 0.8, 2)
        self.assertEqual(
            self.picking.declared_value_currency_id,
            self.sale.currency_id,
        )

    def test_declared_value_partial_delivery(self):
        """Shipping half the quantity halves the declared value base."""
        self.carrier.declared_value_percentage = 100.0
        sale_line = self.picking.move_ids.sale_line_id
        unit_price = sale_line.price_total / sale_line.product_uom_qty
        self.picking.move_ids.quantity = sale_line.product_uom_qty / 2.0
        self.picking.invalidate_recordset(["declared_value"])
        expected = unit_price * (sale_line.product_uom_qty / 2.0)
        self.assertAlmostEqual(self.picking.declared_value, expected, 2)

    def test_ups_address_lines(self):
        """Test address line splitting for UPS limits"""
        ups_request = UpsRequest(self.carrier)
        self.partner.street = "12345 Long Street Name That Exceeds UPS Limits"
        self.partner.street2 = "Suite 678"
        address_lines = ups_request._build_address_lines(self.partner)
        self.assertEqual(len(address_lines), 2)
        self.assertEqual(address_lines[0], "12345 Long Street Name That Exceeds")
        self.assertEqual(address_lines[1], "UPS Limits Suite 678")
        # the Exceedssssssssss part should be moved to the second line
        # to avoid cutting the word in the first line
        self.partner.street = "12345 Long Street Name That Exceedssssssssss"
        address_lines = ups_request._build_address_lines(self.partner)
        self.assertEqual(len(address_lines), 2)
        self.assertEqual(address_lines[0], "12345 Long Street Name That")
        self.assertEqual(address_lines[1], "Exceedssssssssss Suite 678")
        # A street more long
        self.partner.street += "12345 Long Street Name That Exceedssssssssss"
        address_lines = ups_request._build_address_lines(self.partner)
        self.assertEqual(len(address_lines), 3)
        self.assertEqual(address_lines[0], "12345 Long Street Name That")
        self.assertEqual(address_lines[1], "Exceedssssssssss12345 Long Street")
        self.assertEqual(address_lines[2], "Name That Exceedssssssssss Suite")
        self.partner.street = "12345 Short Street Name"
        address_lines = ups_request._build_address_lines(self.partner)
        self.assertEqual(len(address_lines), 1)
        self.assertEqual(address_lines[0], "12345 Short Street Name Suite 678")

    def test_ups_partner_to_shipping_data_tax_identification_number_limit(self):
        """Do not send TaxIdentificationNumber values rejected by UPS length limit."""
        ups_request = UpsRequest(self.carrier)
        self.partner.with_context(no_vat_validation=True).write({"vat": "X" * 16})
        shipping_data = ups_request._partner_to_shipping_data(self.partner)
        self.assertNotIn("TaxIdentificationNumber", shipping_data)

    def test_ups_partner_to_shipping_data_tax_identification_number_sanitized(self):
        """Send valid-length tax ids without whitespace."""
        ups_request = UpsRequest(self.carrier)
        self.partner.with_context(no_vat_validation=True).write(
            {"vat": "IT 12345678901"}
        )
        shipping_data = ups_request._partner_to_shipping_data(self.partner)
        self.assertEqual(shipping_data["TaxIdentificationNumber"], "IT12345678901")


class TestResidentialAddress(TestDeliveryUpsBase):
    @classmethod
    def setUpClass(self):
        super().setUpClass()
        # Base partner (parent company)
        self.company_partner = self.env["res.partner"].create(
            {
                "name": "ABC Pvt Ltd",
                "is_company": True,
                "company_name": "ABC Pvt Ltd",
                "country_id": self.company.country_id.id,
                "phone": self.company.partner_id.phone,
                "email": "test123@odoo.com",
                "street": self.company.partner_id.street,
                "city": self.company.partner_id.city,
                "zip": self.company.partner_id.zip,
                "state_id": self.company.partner_id.state_id.id,
            }
        )

        # Individual partner with no company
        self.individual_partner = self.env["res.partner"].create(
            {
                "name": "John Doe",
                "is_company": False,
                "company_name": False,
                "street": "456 Housing Colony",
                "city": "Brussels",
                "state_id": self.company.partner_id.state_id.id,
                "zip": "12345",
                "country_id": self.company.country_id.id,
                "phone": "3454657",
                "email": "john@example.com",
            }
        )
        self.private_partner = self.env["res.partner"].create(
            {
                "name": "John Doe",
                "type": "other",
                "is_company": False,
                "company_name": False,
                "street": "456 Housing Colony",
                "city": "Brussels",
                "state_id": self.company.partner_id.state_id.id,
                "zip": "12345",
                "country_id": self.company.country_id.id,
                "phone": "3454657",
                "email": "john@example.com",
            }
        )

    def test_is_ups_residential_address_individual(self):
        self.assertTrue(
            self.individual_partner._is_ups_residential_address(),
            "Individual with no company should be residential",
        )

    def test_is_ups_residential_address_private_type(self):
        self.assertTrue(
            self.private_partner._is_ups_residential_address(),
            "Partner of type 'private' should be residential",
        )

    def test_is_ups_residential_address_commercial(self):
        self.assertFalse(
            self.company_partner._is_ups_residential_address(),
            "Company partner should not be residential",
        )

    def test_partner_to_shipping_data_contains_residential(self):
        ups_request = UpsRequest(self.carrier)
        shipping_data = ups_request._partner_to_shipping_data(
            self.individual_partner, is_ship_to=True
        )
        self.assertIn(
            "ResidentialAddressIndicator",
            shipping_data["Address"],
            "ResidentialAddressIndicator should be in shipping data",
        )

    def test_partner_to_shipping_data_commercial(self):
        ups_request = UpsRequest(self.carrier)
        shipping_data = ups_request._partner_to_shipping_data(
            self.company_partner, is_ship_to=True
        )
        self.assertNotIn(
            "ResidentialAddressIndicator",
            shipping_data["Address"],
            "Commercial address should not contain ResidentialAddressIndicator",
        )

    def test_partner_to_shipping_data_residential_only_for_ship_to(self):
        """UPS rejects ResidentialAddressIndicator outside of the ShipTo address."""
        ups_request = UpsRequest(self.carrier)
        shipping_data = ups_request._partner_to_shipping_data(self.individual_partner)
        self.assertNotIn(
            "ResidentialAddressIndicator",
            shipping_data["Address"],
            "Only the ShipTo address may carry ResidentialAddressIndicator",
        )

    def test_prepare_create_shipping_residential_only_for_ship_to(self):
        """Shipper and ShipFrom never carry ResidentialAddressIndicator."""
        picking = self.sale.picking_ids[0]
        picking.partner_id = self.individual_partner
        ups_request = UpsRequest(self.carrier)
        shipment = ups_request._prepare_create_shipping(picking)["ShipmentRequest"][
            "Shipment"
        ]
        # A parentless company partner is residential, so the assertions below
        # would pass vacuously if the indicator were merely never built
        self.assertTrue(picking.company_id.partner_id._is_ups_residential_address())
        self.assertIn("ResidentialAddressIndicator", shipment["ShipTo"]["Address"])
        self.assertNotIn("ResidentialAddressIndicator", shipment["Shipper"]["Address"])
        self.assertNotIn("ResidentialAddressIndicator", shipment["ShipFrom"]["Address"])


class TestUpsNegotiatedRates(TestDeliveryUpsBase):
    @classmethod
    def setUpClass(self):
        super().setUpClass()
        self.picking = self.sale.picking_ids[0]
        self.picking.move_ids.quantity = 10
        self.invoice = self.sale._create_invoices()
        self.invoice.action_post()

    def get_mock_rate_response_values(
        self, charges="0", multi_alert=False, negotiated_charges=False
    ):
        alert_110971 = {
            "Code": "110971",
            "Description": "Your invoice may vary from the displayed reference rates",
        }
        response_value = {
            "RateResponse": {
                "Response": {
                    "ResponseStatus": {"Code": "1", "Description": "Success"},
                    "Alert": alert_110971,
                    "TransactionReference": "",
                },
                "RatedShipment": [
                    {
                        "Service": {"Code": "11", "Description": ""},
                        "RatedShipmentAlert": alert_110971,
                        "BillingWeight": {
                            "UnitOfMeasurement": {
                                "Code": "KGS",
                                "Description": "Kilograms",
                            },
                            "Weight": "0.5",
                        },
                        "TransportationCharges": {
                            "CurrencyCode": "EUR",
                            "MonetaryValue": charges,
                        },
                        "ServiceOptionsCharges": {
                            "CurrencyCode": "EUR",
                            "MonetaryValue": "0.00",
                        },
                        "TotalCharges": {
                            "CurrencyCode": "EUR",
                            "MonetaryValue": charges,
                        },
                        "RatedPackage": [{"Weight": "0.1"}],
                        "Zone": "000",
                    }
                ],
            }
        }
        if multi_alert:
            alert_120900 = {
                "Code": "120900",
                "Description": (
                    "User Id and Shipper Number combination is not qualified"
                    " to receive negotiated rates"
                ),
            }
            response_value["RateResponse"]["Response"]["Alert"] = [
                alert_110971,
                alert_120900,
            ]
            response_value["RateResponse"]["RatedShipment"][0]["RatedShipmentAlert"] = [
                alert_110971,
                alert_120900,
            ]
        if negotiated_charges:
            response_value["RateResponse"]["RatedShipment"][0].update(
                {
                    "NegotiatedRateCharges": {
                        "TotalCharge": {
                            "CurrencyCode": "EUR",
                            "MonetaryValue": "16.33",
                        }
                    }
                }
            )
        return response_value

    def get_mock_shipment_rate_response_values(self, negotiated_charges=False):
        response_value = {
            "ShipmentResponse": {
                "Response": {
                    "ResponseStatus": {"Code": "1", "Description": "Success"},
                    "TransactionReference": "",
                },
                "ShipmentResults": {
                    "ShipmentCharges": {
                        "TransportationCharges": {
                            "CurrencyCode": "EUR",
                            "MonetaryValue": "16.49",
                        },
                        "ServiceOptionsCharges": {
                            "CurrencyCode": "EUR",
                            "MonetaryValue": "0.00",
                        },
                        "TotalCharges": {
                            "CurrencyCode": "EUR",
                            "MonetaryValue": "16.49",
                        },
                    },
                    "BillingWeight": {
                        "UnitOfMeasurement": {
                            "Code": "KGS",
                            "Description": "Kilograms",
                        },
                        "Weight": "0.5",
                    },
                    "ShipmentIdentificationNumber": "1ZXXXXXXXXXXXXXXXX",
                    "PackageResults": [
                        {
                            "TrackingNumber": "1ZXXXXXXXXXXXXXXXX",
                            "ServiceOptionsCharges": {
                                "CurrencyCode": "EUR",
                                "MonetaryValue": "0.00",
                            },
                            "ShippingLabel": {
                                "ImageFormat": {"Code": "GIF", "Description": "GIF"},
                                "GraphicImage": "R0lGODlhAQABAIAAAP///"
                                "wAAACwAAAAAAQABAAACAkQBADs=",
                            },
                        }
                    ],
                },
            }
        }
        if negotiated_charges:
            response_value["ShipmentResponse"]["ShipmentResults"].update(
                {
                    "NegotiatedRateCharges": {
                        "TotalCharge": {
                            "CurrencyCode": "EUR",
                            "MonetaryValue": "16.33",
                        }
                    }
                }
            )
        return response_value

    def test_rate_shipment_with_negotiated_rates(self):
        """When negotiated rates are enabled, the rate request must ask for them
        and the returned price must be the negotiated one when available."""
        self.carrier.ups_negotiated_rates = True
        self.sale.currency_id = self.env.ref("base.EUR")
        response_value = self.get_mock_rate_response_values(
            charges="16.49", negotiated_charges=True
        )
        with mock.patch(_provider_class + "._process_reply") as mock_process_reply:
            mock_process_reply.return_value = response_value
            res = self.carrier.ups_rate_shipment(self.sale)
            request_json = mock_process_reply.call_args[1]["json"]
            self.assertEqual(
                "Y",
                request_json["RateRequest"]["Shipment"]["ShipmentRatingOptions"][
                    "NegotiatedRatesIndicator"
                ],
            )
            self.assertTrue(res["success"])
            self.assertEqual(res["price"], 16.33)

    def test_rate_shipment_without_negotiated_rates(self):
        """When negotiated rates are disabled (default), the rate request must not
        ask for them and the standard price is used."""
        self.sale.currency_id = self.env.ref("base.EUR")
        response_value = self.get_mock_rate_response_values(charges="16.49")
        with mock.patch(_provider_class + "._process_reply") as mock_process_reply:
            mock_process_reply.return_value = response_value
            res = self.carrier.ups_rate_shipment(self.sale)
            request_json = mock_process_reply.call_args[1]["json"]
            self.assertNotIn(
                "ShipmentRatingOptions", request_json["RateRequest"]["Shipment"]
            )
            self.assertTrue(res["success"])
            self.assertEqual(res["price"], 16.49)

    def test_send_shipping_with_negotiated_rates(self):
        """When negotiated rates are enabled, the shipping request must ask for
        them and the shipment is recorded with the negotiated price."""
        self.carrier.ups_negotiated_rates = True
        self.picking.action_confirm()
        self.picking.action_assign()
        self.picking.shipping_weight = 10.0
        self.picking.number_of_packages = 1
        response_value = self.get_mock_shipment_rate_response_values(
            negotiated_charges=True
        )
        with mock.patch(_provider_class + "._process_reply") as mock_process_reply:
            mock_process_reply.return_value = response_value
            self.picking.send_to_shipper()
            request_json = mock_process_reply.call_args[1]["json"]
            self.assertEqual(
                "Y",
                request_json["ShipmentRequest"]["Shipment"]["ShipmentRatingOptions"][
                    "NegotiatedRatesIndicator"
                ],
            )
            self.assertEqual(self.picking.carrier_tracking_ref, "1ZXXXXXXXXXXXXXXXX")


class TestSendPaperlessDocuments(TestDeliveryUpsBase):
    def setUp(self):
        super().setUp()
        self.picking = self.sale.picking_ids[0]
        self.picking.move_ids.quantity = 10
        self.picking.action_assign()
        self.carrier.ups_token = "test_token"
        self.carrier.ups_token_expiration_date = datetime.now() + timedelta(hours=1)
        # Create a dummy invoice PDF
        self.dummy_pdf = base64.b64encode(b"%PDF-1.4\n%Fake PDF Content\n%%EOF")
        self.invoice = self.sale._create_invoices()
        self.invoice.action_post()
        self.ship_response = {
            "price": {"CurrencyCode": "USD", "MonetaryValue": "10.0"},
            "ShipmentIdentificationNumber": "123456",
            "labels": [
                {
                    "tracking_ref": "123456",
                    "format_code": "GIF",
                    "datas": base64.b64encode(self.label),
                }
            ],
        }

    def test_prepare_ups_paperless_documents_adds_missing_docs(self):
        result = self.carrier.prepare_ups_paperless_documents(self.picking)
        doc_types = [doc["UserCreatedFormDocumentType"] for doc in result]
        self.assertIn("002", doc_types, "Invoice should be added if missing")
        self.assertIn("010", doc_types, "Packing list should be added if missing")

    def test_ups_paperless_documents_raises_if_document_id_exists(self):
        """Should raise UserError when a document ID already exists"""
        self.picking.ups_document_identifier = "DUMMY_ID"
        with self.assertRaises(UserError):
            self.carrier.send_ups_paperless_documents(self.picking)

    def test_prepare_paperless_documents_raises_if_invoice_missing(self):
        self.picking.sale_id.invoice_ids = False
        with self.assertRaises(UserError):
            self.carrier.send_ups_paperless_documents(self.picking)

    def test_send_paperless_documents_data(self):
        self.picking.ups_paperless_auto_send = True
        self.picking.ups_paperless_document_ids = [
            (
                0,
                0,
                {
                    "file_name": "Paperless Document - 001",
                    "ups_document_type": "003",
                    "ups_paperless_file": self.dummy_pdf,
                },
            ),
            (
                0,
                0,
                {
                    "file_name": "Paperless Document - 002",
                    "ups_document_type": "013",
                    "ups_paperless_file": self.dummy_pdf,
                },
            ),
        ]
        with mock.patch(
            _provider_class + ".send_paperless_documents", return_value="DOC123456789"
        ):
            result = self.carrier.send_ups_paperless_documents(self.picking)
            self.assertIsNotNone(result)

    def test_send_paperless_documents_success(self):
        """A successful upload stores the returned document ID on the picking."""
        ups_request = UpsRequest(self.carrier)
        documents = [
            {
                "UserCreatedFormFileName": "commercial_invoice.pdf",
                "UserCreatedFormFileFormat": "pdf",
                "UserCreatedFormDocumentType": "002",
                "UserCreatedFormFile": self.dummy_pdf.decode("utf-8"),
            }
        ]
        mock_response = mock.Mock()
        mock_response.status_code = 200
        mock_response.text = json.dumps(
            {"UploadResponse": {"FormsHistoryDocumentID": {"DocumentID": ["DOC123"]}}}
        )
        with mock.patch.object(
            ups_request, "_send_request", return_value=mock_response
        ) as mock_send:
            result = ups_request.send_paperless_documents(self.picking, documents)
        self.assertEqual(result, ["DOC123"])
        self.assertEqual(self.picking.ups_document_identifier, "DOC123")
        self.assertIn("/api/paperlessdocuments/v2/upload", mock_send.call_args[0][0])
        upload_request = json.loads(mock_send.call_args[0][2])["UploadRequest"]
        self.assertEqual(
            upload_request["Request"]["TransactionReference"]["CustomerContext"],
            self.picking.name,
        )

    def test_send_paperless_documents_multiple_documents(self):
        """v2 always returns an array; every document ID is kept."""
        ups_request = UpsRequest(self.carrier)
        documents = [
            {
                "UserCreatedFormFileName": "commercial_invoice.pdf",
                "UserCreatedFormFileFormat": "pdf",
                "UserCreatedFormDocumentType": "002",
                "UserCreatedFormFile": self.dummy_pdf.decode("utf-8"),
            },
            {
                "UserCreatedFormFileName": "packing_list.pdf",
                "UserCreatedFormFileFormat": "pdf",
                "UserCreatedFormDocumentType": "010",
                "UserCreatedFormFile": self.dummy_pdf.decode("utf-8"),
            },
        ]
        mock_response = mock.Mock()
        mock_response.status_code = 200
        mock_response.text = json.dumps(
            {
                "UploadResponse": {
                    "FormsHistoryDocumentID": {"DocumentID": ["DOC1", "DOC2"]}
                }
            }
        )
        with mock.patch.object(
            ups_request, "_send_request", return_value=mock_response
        ):
            result = ups_request.send_paperless_documents(self.picking, documents)
        self.assertEqual(result, ["DOC1", "DOC2"])
        self.assertEqual(self.picking.ups_document_identifier, "DOC1,DOC2")
        self.assertEqual(self.picking._get_ups_document_ids(), ["DOC1", "DOC2"])

    def test_get_ups_document_ids_legacy_format(self):
        """Document IDs stored by the v1 implementation are still readable."""
        self.picking.ups_document_identifier = "['DOC1', 'DOC2']"
        self.assertEqual(self.picking._get_ups_document_ids(), ["DOC1", "DOC2"])
        self.picking.ups_document_identifier = "DOC123"
        self.assertEqual(self.picking._get_ups_document_ids(), ["DOC123"])
        self.picking.ups_document_identifier = False
        self.assertEqual(self.picking._get_ups_document_ids(), [])

    def test_send_paperless_documents_refreshes_expired_token(self):
        """An expired token is renewed before the upload is sent."""
        self.carrier.ups_token_expiration_date = datetime.now() - timedelta(hours=1)
        ups_request = UpsRequest(self.carrier)
        documents = [
            {
                "UserCreatedFormFileName": "commercial_invoice.pdf",
                "UserCreatedFormFileFormat": "pdf",
                "UserCreatedFormDocumentType": "002",
                "UserCreatedFormFile": self.dummy_pdf.decode("utf-8"),
            }
        ]
        mock_response = mock.Mock()
        mock_response.status_code = 200
        mock_response.text = json.dumps(
            {"UploadResponse": {"FormsHistoryDocumentID": {"DocumentID": ["DOC123"]}}}
        )
        with (
            mock.patch.object(ups_request, "_get_new_token") as mock_token,
            mock.patch.object(ups_request, "_send_request", return_value=mock_response),
        ):
            result = ups_request.send_paperless_documents(self.picking, documents)
        mock_token.assert_called_once()
        self.assertEqual(result, ["DOC123"])

    def test_send_paperless_documents_retries_on_401(self):
        """A 401 triggers a new token and exactly one retry."""
        ups_request = UpsRequest(self.carrier)
        documents = [
            {
                "UserCreatedFormFileName": "commercial_invoice.pdf",
                "UserCreatedFormFileFormat": "pdf",
                "UserCreatedFormDocumentType": "002",
                "UserCreatedFormFile": self.dummy_pdf.decode("utf-8"),
            }
        ]
        unauthorized = mock.Mock()
        unauthorized.status_code = 401
        success = mock.Mock()
        success.status_code = 200
        success.text = json.dumps(
            {"UploadResponse": {"FormsHistoryDocumentID": {"DocumentID": ["DOC123"]}}}
        )
        with (
            mock.patch.object(ups_request, "_get_new_token") as mock_token,
            mock.patch.object(
                ups_request, "_send_request", side_effect=[unauthorized, success]
            ) as mock_send,
        ):
            result = ups_request.send_paperless_documents(self.picking, documents)
        mock_token.assert_called_once()
        self.assertEqual(mock_send.call_count, 2)
        self.assertEqual(result, ["DOC123"])

    @mute_logger("odoo.addons.delivery_ups_oca.models.ups_request")
    def test_send_paperless_documents_api_error(self):
        """An error response is raised as a UserError with the UPS message."""
        ups_request = UpsRequest(self.carrier)
        documents = [
            {
                "UserCreatedFormFileName": "commercial_invoice.pdf",
                "UserCreatedFormFileFormat": "pdf",
                "UserCreatedFormDocumentType": "002",
                "UserCreatedFormFile": self.dummy_pdf.decode("utf-8"),
            }
        ]
        mock_response = mock.Mock()
        mock_response.status_code = 400
        mock_response.text = json.dumps(
            {"response": {"errors": [{"message": "Invalid shipper number"}]}}
        )
        with mock.patch.object(
            ups_request, "_send_request", return_value=mock_response
        ):
            with self.assertRaises(UserError) as cm:
                ups_request.send_paperless_documents(self.picking, documents)
        self.assertIn("Invalid shipper number", str(cm.exception))

    @mute_logger("odoo.addons.delivery_ups_oca.models.ups_request")
    def test_send_paperless_documents_non_json_error(self):
        """A non-JSON (e.g. HTML 503 from the edge/CDN) response raises a clear
        UserError instead of a confusing JSON decode error."""
        ups_request = UpsRequest(self.carrier)
        documents = [
            {
                "UserCreatedFormFileName": "commercial_invoice.pdf",
                "UserCreatedFormFileFormat": "pdf",
                "UserCreatedFormDocumentType": "002",
                "UserCreatedFormFile": self.dummy_pdf.decode("utf-8"),
            }
        ]
        mock_response = mock.Mock()
        mock_response.status_code = 503
        mock_response.text = (
            "<HTML><HEAD><TITLE>Internal Server Error</TITLE></HEAD>"
            "<BODY><H1>Internal Server Error - Write</H1></BODY></HTML>"
        )
        with mock.patch.object(
            ups_request, "_send_request", return_value=mock_response
        ):
            with self.assertRaises(UserError) as cm:
                ups_request.send_paperless_documents(self.picking, documents)
        self.assertIn("HTTP 503", str(cm.exception))
        self.assertIn("non-JSON", str(cm.exception))
        self.assertFalse(self.picking.ups_document_identifier)

    @mute_logger("odoo.addons.delivery_ups_oca.models.ups_request")
    def test_send_paperless_documents_without_document_id(self):
        """A response without any DocumentID is an error, not a success."""
        ups_request = UpsRequest(self.carrier)
        documents = [
            {
                "UserCreatedFormFileName": "commercial_invoice.pdf",
                "UserCreatedFormFileFormat": "pdf",
                "UserCreatedFormDocumentType": "002",
                "UserCreatedFormFile": self.dummy_pdf.decode("utf-8"),
            }
        ]
        mock_response = mock.Mock()
        mock_response.status_code = 200
        mock_response.text = json.dumps(
            {
                "UploadResponse": {
                    "Response": {
                        "Alert": {"Code": "120900", "Description": "User Id Missing"}
                    }
                }
            }
        )
        with mock.patch.object(
            ups_request, "_send_request", return_value=mock_response
        ):
            with self.assertRaises(UserError) as cm:
                ups_request.send_paperless_documents(self.picking, documents)
        self.assertIn("did not return any Document ID", str(cm.exception))
        self.assertIn("User Id Missing", str(cm.exception))
        self.assertFalse(self.picking.ups_document_identifier)

    def test_prepare_create_shipping_adds_international_forms(self):
        """A retrieved document ID is added as InternationalForms to the request."""
        self.picking.ups_document_identifier = "DOC123"
        self.picking.shipping_weight = 10.0
        self.picking.number_of_packages = 1
        ups_request = UpsRequest(self.carrier)
        vals = ups_request._prepare_create_shipping(self.picking)
        service_options = vals["ShipmentRequest"]["Shipment"]["ShipmentServiceOptions"]
        forms = service_options["InternationalForms"]
        self.assertEqual(forms["FormType"], ["07"])
        self.assertEqual(forms["UserCreatedForm"]["DocumentID"], ["DOC123"])
        # UPS requires Product, with only Description (an array) mandatory
        self.assertTrue(forms["Product"])
        for product in forms["Product"]:
            self.assertIsInstance(product["Description"], list)
            self.assertLessEqual(len(product["Description"][0]), 35)

    def test_prepare_create_shipping_with_cod_and_international_forms(self):
        """COD and paperless documents can be combined on the same shipment."""
        self.carrier.write({"ups_cash_on_delivery": True, "ups_cod_funds_code": "1"})
        self.picking.ups_document_identifier = "DOC1,DOC2"
        self.picking.shipping_weight = 10.0
        self.picking.number_of_packages = 1
        ups_request = UpsRequest(self.carrier)
        vals = ups_request._prepare_create_shipping(self.picking)
        service_options = vals["ShipmentRequest"]["Shipment"]["ShipmentServiceOptions"]
        self.assertIn("COD", service_options)
        self.assertEqual(
            service_options["InternationalForms"]["UserCreatedForm"]["DocumentID"],
            ["DOC1", "DOC2"],
        )

    def test_send_shipping_triggers_paperless_documents(self):
        """_send_shipping sends the paperless documents before shipping."""
        self.picking.ups_paperless_auto_send = True
        self.picking.shipping_weight = 10.0
        self.picking.number_of_packages = 1
        ups_request = UpsRequest(self.carrier)
        shipment_response = {
            "ShipmentResponse": {
                "ShipmentResults": {
                    "ShipmentCharges": {
                        "TotalCharges": {
                            "CurrencyCode": "USD",
                            "MonetaryValue": "10.0",
                        }
                    },
                    "ShipmentIdentificationNumber": "123456",
                    "PackageResults": {
                        "TrackingNumber": "123456",
                        "ShippingLabel": {
                            "ImageFormat": {"Code": "GIF"},
                            "GraphicImage": base64.b64encode(self.label),
                        },
                    },
                }
            }
        }
        with mock.patch.object(
            type(self.carrier), "send_ups_paperless_documents"
        ) as mock_provider:
            with mock.patch.object(
                ups_request, "_process_reply", return_value=shipment_response
            ):
                with mock.patch.object(ups_request, "_raise_for_status"):
                    ups_request._send_shipping(self.picking)
        mock_provider.assert_called_once_with(self.picking)

    def test_button_validate_triggers_paperless_documents(self):
        """Validating an auto-send picking triggers the paperless documents upload."""
        self._prepare_paperless_picking(self.picking)
        with mock.patch(
            _provider_class + "._send_shipping", return_value=self.ship_response
        ):
            with mock.patch.object(
                type(self.carrier), "send_ups_paperless_documents"
            ) as mock_provider:
                self.picking.button_validate()
        mock_provider.assert_called_once_with(self.picking)

    def _prepare_paperless_picking(self, picking):
        picking.move_ids.quantity = 10
        picking.action_assign()
        picking.ups_paperless_auto_send = True
        picking.ups_paperless_document_ids = [
            (
                0,
                0,
                {
                    "file_name": "Paperless Document - 001",
                    "ups_document_type": "003",
                    "ups_paperless_file": self.dummy_pdf,
                },
            )
        ]
        return picking

    @mute_logger("odoo.addons.delivery_ups_oca.models.stock_picking")
    def test_button_validate_blocked_by_paperless_error(self):
        """A failed upload blocks the validation instead of being swallowed."""
        self._prepare_paperless_picking(self.picking)
        # The savepoint stands in for the rollback Odoo does on a UserError
        with self.assertRaises(UserError) as cm:
            with self.env.cr.savepoint():
                with mock.patch(
                    _provider_class + "._send_shipping",
                    return_value=self.ship_response,
                ):
                    with mock.patch.object(
                        type(self.carrier),
                        "send_ups_paperless_documents",
                        side_effect=UserError(
                            "UPS Paperless Documents upload failed (HTTP 503)."
                        ),
                    ):
                        self.picking.button_validate()
        self.assertIn("HTTP 503", str(cm.exception))
        self.assertNotEqual(self.picking.state, "done")
        self.assertFalse(self.picking.carrier_tracking_ref)

    def test_download_ups_paperless_file(self):
        """The download action returns a URL pointing to the stored file."""
        document = self.env["ups.paperless.document"].create(
            {
                "file_name": "invoice.pdf",
                "ups_document_type": "002",
                "ups_paperless_file": self.dummy_pdf,
                "ups_stock_picking_id": self.picking.id,
            }
        )
        action = document.download_ups_paperless_file()
        self.assertEqual(action["type"], "ir.actions.act_url")
        self.assertIn(str(document.id), action["url"])
        self.assertIn("invoice.pdf", action["url"])

    def test_onchange_sets_auto_send(self):
        """Auto-send is toggled based on the carrier's country groups."""
        country_group = self.env["res.country.group"].create(
            {
                "name": "UPS Paperless Test Group",
                "country_ids": [(6, 0, [self.picking.partner_id.country_id.id])],
            }
        )
        # Country in the carrier's groups -> auto-send enabled
        self.carrier.ups_paperless_country_group_ids = [(6, 0, [country_group.id])]
        self.picking._onchange_ups_paperless_auto_send()
        self.assertTrue(self.picking.ups_paperless_auto_send)
        # No matching country group -> auto-send disabled
        self.carrier.ups_paperless_country_group_ids = [(5, 0, 0)]
        self.picking._onchange_ups_paperless_auto_send()
        self.assertFalse(self.picking.ups_paperless_auto_send)

    def test_send_paperless_documents_no_documents(self):
        """Sending without any document raises a UserError."""
        ups_request = UpsRequest(self.carrier)
        with self.assertRaises(UserError):
            ups_request.send_paperless_documents(self.picking, [])


class TestUpsGlobalCheckout(TestDeliveryUpsBase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.us = cls.env.ref("base.us")
        cls.country_group = cls.env["res.country.group"].create(
            {"name": "UPS GC Test", "country_ids": [(6, 0, [cls.us.id])]}
        )
        cls.us_partner = cls.env["res.partner"].create(
            {
                "name": "US Customer",
                "country_id": cls.us.id,
                "city": "New York",
                "zip": "10001",
            }
        )
        cls.quote = {
            "quote_id": "landed_cost_abc123",
            "amount": 25.0,
            "currency": cls.env.ref("base.main_company").currency_id.name,
            "guarantee_code": "GUARANTEED",
        }

    def test_country_group_data(self):
        group = self.env.ref("delivery_ups_oca.country_group_ups_global_checkout")
        self.assertEqual(group.name, "UPS Global Checkout destinations")
        codes = set(group.country_ids.mapped("code"))
        for code in ("US", "DE", "VN", "KR", "PR"):
            self.assertIn(code, codes)
        self.assertEqual(len(group.country_ids), 42)

    def test_eligibility_no_group(self):
        self.carrier.ups_global_checkout_country_group_ids = False
        self.assertFalse(self.carrier._ups_is_global_checkout_eligible(self.us_partner))

    def test_eligibility_country_in_group(self):
        self.carrier.ups_global_checkout_country_group_ids = self.country_group
        self.assertTrue(self.carrier._ups_is_global_checkout_eligible(self.us_partner))

    def test_eligibility_country_not_in_group(self):
        self.carrier.ups_global_checkout_country_group_ids = self.country_group
        other_partner = self.env["res.partner"].create(
            {"name": "BE Customer", "country_id": self.env.ref("base.be").id}
        )
        self.assertFalse(self.carrier._ups_is_global_checkout_eligible(other_partner))

    def _mock_rate(self):
        return mock.patch(
            _provider_class + "._rate_shipment",
            return_value={
                "RateResponse": {
                    "RatedShipment": {
                        "TotalCharges": {
                            "MonetaryValue": 100.0,
                            "CurrencyCode": self.quote["currency"],
                        }
                    }
                }
            },
        )

    def test_rate_shipment_keeps_price_and_stores_quote(self):
        self.carrier.ups_global_checkout_country_group_ids = self.country_group
        self.sale.partner_shipping_id = self.us_partner
        with (
            self._mock_rate(),
            mock.patch(_provider_class + ".landed_cost_quote", return_value=self.quote),
        ):
            res = self.carrier.ups_rate_shipment(self.sale)
        self.assertTrue(res["success"])
        # The landed cost is NOT added to the shipping price.
        self.assertEqual(res["price"], 100.0)
        self.assertEqual(
            self.sale.ups_landed_cost_quote_identifier, self.quote["quote_id"]
        )
        self.assertEqual(self.sale.ups_landed_cost_amount, 25.0)

    def test_rate_shipment_landed_cost_business_error_surfaces(self):
        self.carrier.ups_global_checkout_country_group_ids = self.country_group
        self.sale.partner_shipping_id = self.us_partner
        with (
            self._mock_rate(),
            mock.patch(
                _provider_class + ".landed_cost_quote",
                side_effect=UserError("no quote"),
            ),
        ):
            res = self.carrier.ups_rate_shipment(self.sale)
        self.assertFalse(res["success"])
        self.assertIn("no quote", res["error_message"])
        self.assertFalse(self.sale.ups_landed_cost_quote_identifier)

    def test_rate_shipment_landed_cost_network_error_propagates(self):
        self.carrier.ups_global_checkout_country_group_ids = self.country_group
        self.sale.partner_shipping_id = self.us_partner
        with (
            self._mock_rate(),
            mock.patch(
                _provider_class + ".landed_cost_quote",
                side_effect=requests.exceptions.ConnectionError("boom"),
            ),
        ):
            with self.assertRaises(requests.exceptions.ConnectionError):
                self.carrier.ups_rate_shipment(self.sale)

    def test_create_delivery_line_adds_landed_cost_line(self):
        self.carrier.ups_landed_cost_product_id = self.env["product.product"].create(
            {"name": "UPS Duties", "type": "service"}
        )
        self.sale.write(
            {
                "ups_landed_cost_quote_identifier": self.quote["quote_id"],
                "ups_landed_cost_amount": 25.0,
            }
        )
        delivery_sol = self.sale._create_delivery_line(self.carrier, 100.0)
        lc_lines = self.sale.order_line.filtered("is_ups_landed_cost")
        self.assertEqual(len(lc_lines), 1)
        self.assertEqual(lc_lines.price_unit, 25.0)
        self.assertFalse(lc_lines.is_delivery)
        self.assertEqual(lc_lines.sequence, delivery_sol.sequence + 1)

    def test_no_landed_cost_line_without_product(self):
        self.carrier.ups_landed_cost_product_id = False
        self.sale.write(
            {
                "ups_landed_cost_quote_identifier": self.quote["quote_id"],
                "ups_landed_cost_amount": 25.0,
            }
        )
        self.sale._create_delivery_line(self.carrier, 100.0)
        self.assertFalse(self.sale.order_line.filtered("is_ups_landed_cost"))

    def test_no_landed_cost_line_without_quote(self):
        self.carrier.ups_landed_cost_product_id = self.env["product.product"].create(
            {"name": "UPS Duties", "type": "service"}
        )
        self.sale.write(
            {"ups_landed_cost_quote_identifier": False, "ups_landed_cost_amount": 0.0}
        )
        self.sale._create_delivery_line(self.carrier, 100.0)
        self.assertFalse(self.sale.order_line.filtered("is_ups_landed_cost"))

    def test_create_delivery_line_no_duplicate_landed_cost(self):
        self.carrier.ups_landed_cost_product_id = self.env["product.product"].create(
            {"name": "UPS Duties", "type": "service"}
        )
        self.sale.write(
            {
                "ups_landed_cost_quote_identifier": self.quote["quote_id"],
                "ups_landed_cost_amount": 25.0,
            }
        )
        self.sale._create_delivery_line(self.carrier, 100.0)
        self.sale._create_delivery_line(self.carrier, 100.0)
        self.assertEqual(len(self.sale.order_line.filtered("is_ups_landed_cost")), 1)

    def test_remove_delivery_line_removes_landed_cost_line(self):
        self.carrier.ups_landed_cost_product_id = self.env["product.product"].create(
            {"name": "UPS Duties", "type": "service"}
        )
        self.sale.write(
            {
                "ups_landed_cost_quote_identifier": self.quote["quote_id"],
                "ups_landed_cost_amount": 25.0,
            }
        )
        self.sale._create_delivery_line(self.carrier, 100.0)
        self.assertTrue(self.sale.order_line.filtered("is_ups_landed_cost"))
        self.sale._remove_delivery_line()
        self.assertFalse(self.sale.order_line.filtered("is_ups_landed_cost"))

    def test_picking_copies_quote_id(self):
        self.sale.ups_landed_cost_quote_identifier = self.quote["quote_id"]
        picking = self.env["stock.picking"].create(
            {
                "partner_id": self.us_partner.id,
                "picking_type_id": self.env.ref("stock.picking_type_out").id,
                "location_id": self.env.ref("stock.stock_location_stock").id,
                "location_dest_id": self.env.ref("stock.stock_location_customers").id,
                "carrier_id": self.carrier.id,
                "sale_id": self.sale.id,
            }
        )
        self.assertEqual(
            picking.ups_landed_cost_quote_identifier, self.quote["quote_id"]
        )

    def _add_landed_cost_line(self, order):
        return self.env["sale.order.line"].create(
            {
                "order_id": order.id,
                "name": "UPS Duties, Taxes & Fees",
                "product_id": self.product.id,
                "product_uom_qty": 1,
                "price_unit": 25.0,
                "is_ups_landed_cost": True,
            }
        )

    def test_prepare_shipping_ddp_keeps_paperless_document_ids(self):
        picking = self.sale.picking_ids[0]
        picking.ups_landed_cost_quote_identifier = self.quote["quote_id"]
        picking.ups_document_identifier = "DOC1,DOC2"
        self._add_landed_cost_line(self.sale)
        picking.move_ids.quantity = 10
        picking.number_of_packages = 1
        vals = UpsRequest(self.carrier)._prepare_create_shipping(picking)
        forms = vals["ShipmentRequest"]["Shipment"]["ShipmentServiceOptions"][
            "InternationalForms"
        ]
        self.assertEqual(forms["FormType"], ["01", "07"])
        self.assertEqual(forms["UserCreatedForm"]["DocumentID"], ["DOC1", "DOC2"])
        self.assertIsInstance(forms["Product"][0]["Description"], list)
        self.assertIn("Unit", forms["Product"][0])

    def _prepare_ddp_paperless_forms(self, with_invoice=True):
        picking = self.sale.picking_ids[0]
        picking.ups_document_identifier = "DOC1"
        if with_invoice:
            self.env["ups.paperless.document"].create(
                {
                    "ups_paperless_file": "dGVzdA==",
                    "file_name": "invoice.pdf",
                    "ups_document_type": "002",
                    "ups_stock_picking_id": picking.id,
                }
            )
        picking.ups_landed_cost_quote_identifier = self.quote["quote_id"]
        self._add_landed_cost_line(self.sale)
        picking.move_ids.quantity = 10
        picking.number_of_packages = 1
        vals = UpsRequest(self.carrier)._prepare_create_shipping(picking)
        return vals["ShipmentRequest"]["Shipment"]["ShipmentServiceOptions"][
            "InternationalForms"
        ]

    def test_prepare_shipping_global_checkout_uploaded_invoice_skips_ups_invoice(
        self,
    ):
        forms = self._prepare_ddp_paperless_forms()
        self.assertEqual(forms["FormType"], ["07"])
        self.assertEqual(forms["UserCreatedForm"]["DocumentID"], ["DOC1"])
        self.assertNotIn("InvoiceNumber", forms)
        # Commodity data matching the quote is still sent.
        self.assertEqual(forms["CurrencyCode"], self.sale.currency_id.name)
        self.assertIn("Number", forms["Product"][0]["Unit"])
        self.assertIn("Value", forms["Product"][0]["Unit"])

    def test_prepare_shipping_global_checkout_without_invoice_keeps_ups_invoice(
        self,
    ):
        forms = self._prepare_ddp_paperless_forms(with_invoice=False)
        self.assertEqual(forms["FormType"], ["01", "07"])
        self.assertIn("InvoiceNumber", forms)

    def test_prepare_shipping_includes_quote_id_and_ddp(self):
        picking = self.sale.picking_ids[0]
        picking.ups_landed_cost_quote_identifier = self.quote["quote_id"]
        self._add_landed_cost_line(self.sale)
        picking.move_ids.quantity = 10
        picking.number_of_packages = 1
        ups_request = UpsRequest(self.carrier)
        vals = ups_request._prepare_create_shipping(picking)
        shipment = vals["ShipmentRequest"]["Shipment"]
        self.assertEqual(shipment["QuoteID"], self.quote["quote_id"])
        charges = shipment["PaymentInformation"]["ShipmentCharge"]
        self.assertTrue(any(c.get("Type") == "02" for c in charges))
        forms = shipment["ShipmentServiceOptions"]["InternationalForms"]
        self.assertEqual(forms["FormType"], ["01"])
        self.assertEqual(forms["ReasonForExport"], "SALE")
        self.assertTrue(forms["InvoiceNumber"])
        self.assertEqual(forms["CurrencyCode"], self.sale.currency_id.name)
        sold_to = forms["Contacts"]["SoldTo"]
        self.assertTrue(sold_to["Name"])
        self.assertTrue(sold_to["AttentionName"])
        self.assertEqual(
            sold_to["Address"]["CountryCode"],
            picking.partner_id.country_id.code,
        )
        self.assertNotIn("ResidentialAddressIndicator", sold_to["Address"])
        self.assertTrue(forms["Product"])
        product = forms["Product"][0]
        self.assertIn("Number", product["Unit"])
        self.assertIn("Value", product["Unit"])

    def test_send_to_shipper_posts_duties_message(self):
        self.sale.ups_landed_cost_amount = 83.31
        picking = self.sale.picking_ids[0]
        picking.ups_landed_cost_quote_identifier = self.quote["quote_id"]
        picking.action_confirm()
        picking.action_assign()
        label = b"%PDF-1.4\n%EOF"
        with mock.patch(
            _provider_class + "._send_shipping",
            return_value={
                "price": {"CurrencyCode": "USD", "MonetaryValue": "0.0"},
                "ShipmentIdentificationNumber": "123456",
                "labels": [
                    {
                        "tracking_ref": "123456",
                        "format_code": "png",
                        "datas": base64.b64encode(label),
                    }
                ],
            },
        ):
            picking.send_to_shipper()
        messages = picking.message_ids.mapped("body")
        self.assertTrue(
            any("Duties, Taxes" in (m or "") and "83.31" in (m or "") for m in messages)
        )

    def test_prepare_shipping_quote_id_falls_back_to_order(self):
        picking = self.sale.picking_ids[0]
        picking.ups_landed_cost_quote_identifier = False
        self.sale.ups_landed_cost_quote_identifier = self.quote["quote_id"]
        self._add_landed_cost_line(self.sale)
        picking.move_ids.quantity = 10
        picking.number_of_packages = 1
        ups_request = UpsRequest(self.carrier)
        vals = ups_request._prepare_create_shipping(picking)
        shipment = vals["ShipmentRequest"]["Shipment"]
        self.assertEqual(shipment["QuoteID"], self.quote["quote_id"])
        # The quote id is persisted onto the picking.
        self.assertEqual(
            picking.ups_landed_cost_quote_identifier, self.quote["quote_id"]
        )

    def test_prepare_shipping_no_ddp_when_landed_cost_line_removed(self):
        picking = self.sale.picking_ids[0]
        picking.ups_landed_cost_quote_identifier = self.quote["quote_id"]
        self.sale.ups_landed_cost_quote_identifier = self.quote["quote_id"]
        # No is_ups_landed_cost line on the order: the customer is not charged
        # duties, so the shipment must not apply DDP.
        picking.move_ids.quantity = 10
        picking.number_of_packages = 1
        ups_request = UpsRequest(self.carrier)
        vals = ups_request._prepare_create_shipping(picking)
        shipment = vals["ShipmentRequest"]["Shipment"]
        self.assertNotIn("QuoteID", shipment)
        self.assertNotIn(
            "InternationalForms", shipment.get("ShipmentServiceOptions", {})
        )
        charges = shipment["PaymentInformation"]["ShipmentCharge"]
        if isinstance(charges, dict):
            charges = [charges]
        self.assertFalse(any(c.get("Type") == "02" for c in charges))
        # The picking quote id is cleared and a note is posted.
        self.assertFalse(picking.ups_landed_cost_quote_identifier)
        self.assertTrue(
            any(
                "DDP was not applied" in (m or "")
                for m in picking.message_ids.mapped("body")
            )
        )

    def test_prepare_shipping_standalone_picking_quote_id_enforces_ddp(self):
        picking = self.sale.picking_ids[0]
        picking.ups_landed_cost_quote_identifier = self.quote["quote_id"]
        # Detach from the sale order (manually created delivery order).
        picking.sale_id = False
        picking.move_ids.quantity = 10
        picking.number_of_packages = 1
        ups_request = UpsRequest(self.carrier)
        vals = ups_request._prepare_create_shipping(picking)
        shipment = vals["ShipmentRequest"]["Shipment"]
        self.assertEqual(shipment["QuoteID"], self.quote["quote_id"])
        charges = shipment["PaymentInformation"]["ShipmentCharge"]
        self.assertTrue(any(c.get("Type") == "02" for c in charges))

    def test_prepare_shipping_destination_mismatch_raises(self):
        self.sale.partner_shipping_id = self.us_partner
        self._add_landed_cost_line(self.sale)
        picking = self.sale.picking_ids[0]
        picking.ups_landed_cost_quote_identifier = self.quote["quote_id"]
        picking.move_ids.quantity = 10
        picking.number_of_packages = 1
        picking.partner_id = self.env["res.partner"].create(
            {"name": "Other Country", "country_id": self.env.ref("base.fr").id}
        )
        ups_request = UpsRequest(self.carrier)
        with self.assertRaises(UserError):
            ups_request._prepare_create_shipping(picking)

    def test_gc_product_hs_code_falls_back_to_core_field(self):
        # Without product_harmonized_system (or without a resolved hs.code),
        # the core stock_delivery hs_code field is used as fallback.
        ups_request = UpsRequest(self.carrier)
        if hasattr(self.product, "get_hs_code_recursively"):
            self.skipTest("product_harmonized_system is installed")
        self.product.product_tmpl_id.hs_code = "610910"
        self.assertEqual(ups_request._gc_product_hs_code(self.product), "610910")

    def test_gc_product_hs_code_uses_local_code(self):
        # With product_harmonized_system, the full local_code is sent.
        if not hasattr(self.product, "get_hs_code_recursively"):
            self.skipTest("product_harmonized_system is not installed")
        hs_code = self.env["hs.code"].create(
            {"local_code": "6109100010", "description": "T-shirts"}
        )
        self.product.product_tmpl_id.hs_code_id = hs_code
        ups_request = UpsRequest(self.carrier)
        self.assertEqual(ups_request._gc_product_hs_code(self.product), "6109100010")

    def test_landed_cost_quote_parses_response(self):
        ups_request = UpsRequest(self.carrier)
        self.sale.partner_shipping_id = self.us_partner
        data = {
            "landedCostCalculateWorkflow": [
                {
                    "id": "landed_cost_xyz",
                    "currencyCode": self.quote["currency"],
                    "landedCostGuaranteeCode": "GUARANTEED",
                    "amountSubtotals": {"landedCostTotal": 42.0},
                }
            ]
        }
        with mock.patch.object(ups_request, "_send_graphql", return_value=data):
            result = ups_request.landed_cost_quote(self.sale, 100.0)
        self.assertEqual(result["quote_id"], "landed_cost_xyz")
        self.assertEqual(result["amount"], 42.0)
        self.assertEqual(result["guarantee_code"], "GUARANTEED")

    def test_landed_cost_quote_no_result_raises(self):
        ups_request = UpsRequest(self.carrier)
        self.sale.partner_shipping_id = self.us_partner
        with mock.patch.object(
            ups_request,
            "_send_graphql",
            return_value={"landedCostCalculateWorkflow": []},
        ):
            with self.assertRaises(UserError):
                ups_request.landed_cost_quote(self.sale, 100.0)

    def _mock_graphql_response(self, ups_request, payload):
        ups_request.token = "valid_token_123"
        ups_request.token_expiration_date = datetime.now() + timedelta(hours=1)
        mock_response = mock.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = payload
        return mock_response

    def test_send_graphql_success(self):
        ups_request = UpsRequest(self.carrier)
        mock_response = self._mock_graphql_response(ups_request, {"data": {"foo": 1}})
        with (
            mock.patch.object(
                ups_request, "_send_request", return_value=mock_response
            ) as mock_send,
            self._patch_carrier_log_xml(),
        ):
            data = ups_request._send_graphql("query { x }", {"a": 1})
        self.assertEqual(data, {"foo": 1})
        call_args = mock_send.call_args
        self.assertTrue(call_args.args[0].endswith("/api/globalcheckout/v1/graphql"))
        self.assertEqual(
            call_args.args[3]["shipperNumber"], self.carrier.ups_shipper_number
        )
        self.assertEqual(call_args.kwargs["timeout"], 10)

    def test_send_graphql_raises_on_errors(self):
        ups_request = UpsRequest(self.carrier)
        mock_response = self._mock_graphql_response(
            ups_request, {"errors": [{"message": "bad request"}]}
        )
        with (
            mock.patch.object(ups_request, "_send_request", return_value=mock_response),
            self._patch_carrier_log_xml(),
        ):
            with self.assertRaises(UserError) as err:
                ups_request._send_graphql("query { x }", skip_errors=False)
        self.assertIn("bad request", str(err.exception))

    def test_raise_for_graphql_errors_skip(self):
        ups_request = UpsRequest(self.carrier)
        logger = "odoo.addons.delivery_ups_oca.models.ups_request"
        with self.assertLogs(logger, level="INFO") as log_catcher:
            # Should not raise when skip_errors=True.
            ups_request._raise_for_graphql_errors(
                {"errors": [{"message": "ignored"}]}, skip_errors=True
            )
        self.assertTrue(any("ignored" in msg for msg in log_catcher.output))

    def test_gc_party_and_item_inputs(self):
        ups_request = UpsRequest(self.carrier)
        self.sale.partner_shipping_id = self.us_partner
        self.product.default_code = "SKU-1"
        parties = ups_request._gc_party_inputs(self.sale)
        self.assertEqual([p["type"] for p in parties], ["ORIGIN", "DESTINATION"])
        destination = parties[1]["location"]
        self.assertEqual(destination["countryCode"], self.us.code)
        self.assertEqual(destination["postalCode"], self.us_partner.zip)
        items = ups_request._gc_item_inputs(self.sale)
        self.assertEqual(len(items), 1)
        item = items[0]
        self.assertEqual(item["quantity"], 10)
        self.assertEqual(item["currencyCode"], self.sale.currency_id.name)
        self.assertEqual(item["productId"], "SKU-1")
        self.assertTrue(item["description"])

    def test_gc_commodities_excludes_service_products(self):
        service = self.env["product.product"].create(
            {"name": "Warranty", "type": "service"}
        )
        self.env["sale.order.line"].create(
            {
                "order_id": self.sale.id,
                "product_id": service.id,
                "product_uom_qty": 1,
                "price_unit": 50.0,
            }
        )
        ups_request = UpsRequest(self.carrier)
        commodities = ups_request._gc_commodities(self.sale)
        descriptions = [c["description"] for c in commodities]
        self.assertNotIn("Warranty", descriptions)
        self.assertTrue(
            any(self.product.name == d for d in descriptions),
            "Physical product must still be included",
        )

    def test_gc_commodities_excludes_zero_quantity_lines(self):
        removed_product = self.env["product.product"].create(
            {"name": "Removed product", "type": "consu", "is_storable": True}
        )
        line = self.env["sale.order.line"].create(
            {
                "order_id": self.sale.id,
                "product_id": removed_product.id,
                "product_uom_qty": 1,
                "price_unit": 50.0,
            }
        )
        line.product_uom_qty = 0
        ups_request = UpsRequest(self.carrier)
        commodities = ups_request._gc_commodities(self.sale)
        self.assertEqual([c["description"] for c in commodities], [self.product.name])
        self.assertEqual(commodities[0]["quantity"], 10)
        items = ups_request._gc_item_inputs(self.sale)
        self.assertEqual([i["description"] for i in items], [self.product.name])

    def test_gc_commodities_product_id_falls_back_to_barcode(self):
        self.product.default_code = False
        self.product.barcode = "1234567890123"
        ups_request = UpsRequest(self.carrier)
        commodities = ups_request._gc_commodities(self.sale)
        self.assertTrue(commodities)
        self.assertEqual(commodities[0]["product_id"], "1234567890123")

    def test_wizard_shows_landed_cost(self):
        self.sale.ups_landed_cost_amount = 25.0
        wizard = self.env["choose.delivery.carrier"].create(
            {"order_id": self.sale.id, "carrier_id": self.carrier.id}
        )
        self.assertEqual(wizard.ups_landed_cost_amount, 25.0)

    def test_landed_cost_quote_maps_service_level(self):
        ups_request = UpsRequest(self.carrier)
        self.sale.partner_shipping_id = self.us_partner
        data = {
            "landedCostCalculateWorkflow": [
                {
                    "id": "landed_cost_xyz",
                    "currencyCode": self.quote["currency"],
                    "landedCostGuaranteeCode": "GUARANTEED",
                    "amountSubtotals": {"landedCostTotal": 42.0},
                }
            ]
        }
        with mock.patch.object(
            ups_request, "_send_graphql", return_value=data
        ) as mock_send:
            ups_request.landed_cost_quote(self.sale, 100.0)
        variables = mock_send.call_args.args[1]
        self.assertEqual(variables["rating"]["serviceLevelCode"], "ups.standard")

    def test_landed_cost_quote_unsupported_service_raises(self):
        self.carrier.ups_service_code = "01"  # Next Day Air (domestic)
        ups_request = UpsRequest(self.carrier)
        self.sale.partner_shipping_id = self.us_partner
        with self.assertRaises(UserError):
            ups_request.landed_cost_quote(self.sale, 100.0)

    def test_copied_order_keeps_landed_cost_flag(self):
        tariff_product = self.env["product.product"].create(
            {"name": "UPS Duties", "type": "service"}
        )
        self.carrier.ups_landed_cost_product_id = tariff_product
        self.sale.write(
            {
                "ups_landed_cost_quote_identifier": self.quote["quote_id"],
                "ups_landed_cost_amount": 25.0,
            }
        )
        self.sale._create_delivery_line(self.carrier, 100.0)
        new_order = self.sale.copy()
        lc_lines = new_order.order_line.filtered("is_ups_landed_cost")
        self.assertEqual(len(lc_lines), 1)
        ups_request = UpsRequest(self.carrier)
        commodities = ups_request._gc_commodities(new_order)
        self.assertFalse(any(c["description"] == "UPS Duties" for c in commodities))

    def test_gc_carton_inputs(self):
        ups_request = UpsRequest(self.carrier)
        cartons = ups_request._gc_carton_inputs(self.sale)
        self.assertEqual(len(cartons), 1)
        carton = cartons[0]
        self.assertEqual(carton["dimensionalUnit"], "INCH")
        self.assertEqual(carton["weightUnit"], "POUND")
        self.assertEqual(carton["type"], "PACKAGE")
        self.assertGreater(carton["weight"], 0)


class TestUpsLandedCostEstimate(TestDeliveryUpsBase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.be = cls.env.ref("base.be")
        cls.country_group = cls.env["res.country.group"].create(
            {"name": "UPS LC Estimate Test", "country_ids": [(6, 0, [cls.be.id])]}
        )
        cls.be_partner = cls.env["res.partner"].create(
            {
                "name": "BE Customer",
                "country_id": cls.be.id,
                "city": "Brussels",
                "zip": "1000",
            }
        )
        cls.currency_name = cls.env.ref("base.main_company").currency_id.name
        cls.estimate = {
            "amount": 42.0,
            "duties": 20.0,
            "vat": 18.0,
            "brokerage": 4.0,
            "currency": cls.currency_name,
            "identifier": "LC123",
        }
        cls.shipment_response = {
            "transID": "LC123",
            "shipment": {
                "currencyCode": cls.currency_name,
                "grandTotal": 42.0,
                "totalDuties": 20.0,
                "totalVAT": 18.0,
                "totalBrokerageFees": 4.0,
            },
        }

    def _mock_rate(self):
        return mock.patch(
            _provider_class + "._rate_shipment",
            return_value={
                "RateResponse": {
                    "RatedShipment": {
                        "TotalCharges": {
                            "MonetaryValue": 100.0,
                            "CurrencyCode": self.currency_name,
                        }
                    }
                }
            },
        )

    def test_eligibility_no_group(self):
        self.carrier.ups_landed_cost_estimate_country_group_ids = False
        self.assertFalse(
            self.carrier._ups_is_landed_cost_estimate_eligible(self.be_partner)
        )

    def test_eligibility_country_in_group(self):
        self.carrier.ups_landed_cost_estimate_country_group_ids = self.country_group
        self.assertTrue(
            self.carrier._ups_is_landed_cost_estimate_eligible(self.be_partner)
        )

    def test_global_checkout_takes_precedence(self):
        self.carrier.ups_landed_cost_estimate_country_group_ids = self.country_group
        self.carrier.ups_global_checkout_country_group_ids = self.country_group
        self.assertFalse(
            self.carrier._ups_is_landed_cost_estimate_eligible(self.be_partner)
        )

    def test_rate_shipment_keeps_price_and_stores_estimate(self):
        self.carrier.ups_landed_cost_estimate_country_group_ids = self.country_group
        self.sale.partner_shipping_id = self.be_partner
        with (
            self._mock_rate(),
            mock.patch(
                _provider_class + ".landed_cost_quote_estimate",
                return_value=self.estimate,
            ),
        ):
            res = self.carrier.ups_rate_shipment(self.sale)
        self.assertTrue(res["success"])
        self.assertEqual(res["price"], 100.0)
        self.assertEqual(self.sale.ups_landed_cost_estimate_amount, 42.0)

    def test_rate_shipment_applies_margin(self):
        self.carrier.ups_landed_cost_estimate_country_group_ids = self.country_group
        self.carrier.ups_landed_cost_estimate_margin = 10.0
        self.sale.partner_shipping_id = self.be_partner
        with (
            self._mock_rate(),
            mock.patch(
                _provider_class + ".landed_cost_quote_estimate",
                return_value=self.estimate,
            ),
        ):
            self.carrier.ups_rate_shipment(self.sale)
        self.assertAlmostEqual(self.sale.ups_landed_cost_estimate_amount, 46.2)

    def test_margin_negative_raises(self):
        with self.assertRaises(ValidationError):
            self.carrier.ups_landed_cost_estimate_margin = -5.0

    def test_rate_shipment_estimate_skipped_when_gc_eligible(self):
        self.carrier.ups_landed_cost_estimate_country_group_ids = self.country_group
        self.carrier.ups_global_checkout_country_group_ids = self.country_group
        self.sale.partner_shipping_id = self.be_partner
        with (
            self._mock_rate(),
            mock.patch(
                _provider_class + ".landed_cost_quote",
                return_value={
                    "quote_id": "q1",
                    "amount": 30.0,
                    "currency": self.currency_name,
                    "guarantee_code": "GUARANTEED",
                },
            ),
            mock.patch(
                _provider_class + ".landed_cost_quote_estimate"
            ) as mock_estimate,
        ):
            self.carrier.ups_rate_shipment(self.sale)
        mock_estimate.assert_not_called()
        self.assertFalse(self.sale.ups_landed_cost_estimate_amount)

    def test_landed_cost_estimate_request(self):
        self.sale.partner_shipping_id = self.be_partner
        ups_request = UpsRequest(self.carrier)
        with mock.patch.object(
            ups_request, "_process_reply", return_value=self.shipment_response
        ):
            result = ups_request.landed_cost_quote_estimate(self.sale, 100.0)
        self.assertEqual(result["amount"], 42.0)
        self.assertEqual(result["duties"], 20.0)
        self.assertEqual(result["vat"], 18.0)
        self.assertEqual(result["brokerage"], 4.0)
        self.assertEqual(result["currency"], self.currency_name)
        self.assertEqual(result["identifier"], "LC123")

    def test_landed_cost_estimate_error_surfaces(self):
        self.sale.partner_shipping_id = self.be_partner
        ups_request = UpsRequest(self.carrier)
        with mock.patch.object(
            ups_request,
            "_process_reply",
            return_value={"error": [{"code": "1", "message": "bad"}]},
        ):
            with self.assertRaises(UserError):
                ups_request.landed_cost_quote_estimate(self.sale, 100.0)

    def test_estimate_line_created(self):
        self.carrier.ups_landed_cost_estimate_product_id = self.env[
            "product.product"
        ].create({"name": "UPS Estimated Duties", "type": "service"})
        self.sale.ups_landed_cost_estimate_amount = 42.0
        delivery_sol = self.sale._create_delivery_line(self.carrier, 100.0)
        lines = self.sale.order_line.filtered("is_ups_landed_cost_estimate")
        self.assertEqual(len(lines), 1)
        self.assertEqual(lines.price_unit, 42.0)
        self.assertEqual(lines.sequence, delivery_sol.sequence + 1)

    def test_no_estimate_line_without_product(self):
        self.carrier.ups_landed_cost_estimate_product_id = False
        self.sale.ups_landed_cost_estimate_amount = 42.0
        self.sale._create_delivery_line(self.carrier, 100.0)
        self.assertFalse(self.sale.order_line.filtered("is_ups_landed_cost_estimate"))

    def test_no_duplicate_estimate_line(self):
        self.carrier.ups_landed_cost_estimate_product_id = self.env[
            "product.product"
        ].create({"name": "UPS Estimated Duties", "type": "service"})
        self.sale.ups_landed_cost_estimate_amount = 42.0
        self.sale._create_delivery_line(self.carrier, 100.0)
        self.sale._create_delivery_line(self.carrier, 100.0)
        self.assertEqual(
            len(self.sale.order_line.filtered("is_ups_landed_cost_estimate")), 1
        )

    def test_remove_delivery_line_removes_estimate_line(self):
        self.carrier.ups_landed_cost_estimate_product_id = self.env[
            "product.product"
        ].create({"name": "UPS Estimated Duties", "type": "service"})
        self.sale.ups_landed_cost_estimate_amount = 42.0
        self.sale._create_delivery_line(self.carrier, 100.0)
        self.assertTrue(self.sale.order_line.filtered("is_ups_landed_cost_estimate"))
        self.sale._remove_delivery_line()
        self.assertFalse(self.sale.order_line.filtered("is_ups_landed_cost_estimate"))

    def test_wizard_shows_landed_cost_estimate(self):
        self.sale.ups_landed_cost_estimate_amount = 242.78
        wizard = self.env["choose.delivery.carrier"].create(
            {"order_id": self.sale.id, "carrier_id": self.carrier.id}
        )
        self.assertEqual(wizard.ups_landed_cost_estimate_amount, 242.78)

    def test_commodities_exclude_estimate_line(self):
        self.carrier.ups_landed_cost_estimate_product_id = self.env[
            "product.product"
        ].create({"name": "UPS Estimated Duties", "type": "service"})
        self.sale.ups_landed_cost_estimate_amount = 42.0
        self.sale._create_delivery_line(self.carrier, 100.0)
        self.assertTrue(self.sale.order_line.filtered("is_ups_landed_cost_estimate"))
        ups_request = UpsRequest(self.carrier)
        commodities = ups_request._gc_commodities(self.sale)
        self.assertFalse(
            any(c["description"] == "UPS Estimated Duties" for c in commodities)
        )

    def _add_estimate_line(self, order):
        return self.env["sale.order.line"].create(
            {
                "order_id": order.id,
                "name": "UPS Estimated Duties, Taxes & Fees",
                "product_id": self.product.id,
                "product_uom_qty": 1,
                "price_unit": 42.0,
                "is_ups_landed_cost_estimate": True,
            }
        )

    def _prepare_estimate_paperless_forms(self, with_invoice=True):
        picking = self.sale.picking_ids[0]
        picking.ups_document_identifier = "DOC1"
        if with_invoice:
            self.env["ups.paperless.document"].create(
                {
                    "ups_paperless_file": "dGVzdA==",
                    "file_name": "invoice.pdf",
                    "ups_document_type": "002",
                    "ups_stock_picking_id": picking.id,
                }
            )
        self.carrier.ups_landed_cost_estimate_ddp = True
        self.sale.ups_landed_cost_estimate_amount = 42.0
        self._add_estimate_line(self.sale)
        picking.move_ids.quantity = 10
        picking.number_of_packages = 1
        vals = UpsRequest(self.carrier)._prepare_create_shipping(picking)
        return vals["ShipmentRequest"]["Shipment"]["ShipmentServiceOptions"][
            "InternationalForms"
        ]

    def test_prepare_shipping_estimate_uploaded_invoice_skips_ups_invoice(self):
        forms = self._prepare_estimate_paperless_forms()
        self.assertEqual(forms["FormType"], ["07"])
        self.assertEqual(forms["UserCreatedForm"]["DocumentID"], ["DOC1"])
        self.assertNotIn("InvoiceNumber", forms)
        # Commodity data is still sent for DDP duty calculation.
        self.assertEqual(forms["CurrencyCode"], self.sale.currency_id.name)
        self.assertIn("Number", forms["Product"][0]["Unit"])
        self.assertIn("Value", forms["Product"][0]["Unit"])

    def test_prepare_shipping_estimate_without_invoice_keeps_ups_invoice(self):
        forms = self._prepare_estimate_paperless_forms(with_invoice=False)
        self.assertEqual(forms["FormType"], ["01", "07"])
        self.assertIn("InvoiceNumber", forms)

    def test_ddp_off_no_ddp_applied(self):
        self.carrier.ups_landed_cost_estimate_ddp = False
        self.sale.ups_landed_cost_estimate_amount = 42.0
        self._add_estimate_line(self.sale)
        picking = self.sale.picking_ids[0]
        picking.move_ids.quantity = 10
        picking.number_of_packages = 1
        ups_request = UpsRequest(self.carrier)
        vals = ups_request._prepare_create_shipping(picking)
        shipment = vals["ShipmentRequest"]["Shipment"]
        self.assertNotIn("QuoteID", shipment)
        self.assertNotIn(
            "InternationalForms", shipment.get("ShipmentServiceOptions", {})
        )
        charges = shipment["PaymentInformation"]["ShipmentCharge"]
        if isinstance(charges, dict):
            charges = [charges]
        self.assertFalse(any(c.get("Type") == "02" for c in charges))

    def test_ddp_on_applies_without_quote_id(self):
        self.carrier.ups_landed_cost_estimate_ddp = True
        self.sale.ups_landed_cost_estimate_amount = 42.0
        self._add_estimate_line(self.sale)
        picking = self.sale.picking_ids[0]
        picking.move_ids.quantity = 10
        picking.number_of_packages = 1
        ups_request = UpsRequest(self.carrier)
        vals = ups_request._prepare_create_shipping(picking)
        shipment = vals["ShipmentRequest"]["Shipment"]
        # No Quote ID for the estimate (not a guaranteed quote).
        self.assertNotIn("QuoteID", shipment)
        charges = shipment["PaymentInformation"]["ShipmentCharge"]
        self.assertTrue(any(c.get("Type") == "02" for c in charges))
        forms = shipment["ShipmentServiceOptions"]["InternationalForms"]
        self.assertEqual(forms["FormType"], ["01"])
        self.assertTrue(forms["Product"])

    def test_ddp_on_without_estimate_line_no_ddp(self):
        self.carrier.ups_landed_cost_estimate_ddp = True
        self.sale.ups_landed_cost_estimate_amount = 42.0
        picking = self.sale.picking_ids[0]
        picking.move_ids.quantity = 10
        picking.number_of_packages = 1
        ups_request = UpsRequest(self.carrier)
        vals = ups_request._prepare_create_shipping(picking)
        shipment = vals["ShipmentRequest"]["Shipment"]
        charges = shipment["PaymentInformation"]["ShipmentCharge"]
        if isinstance(charges, dict):
            charges = [charges]
        self.assertFalse(any(c.get("Type") == "02" for c in charges))

    def test_ddp_on_destination_mismatch_still_applies_ddp(self):
        self.carrier.ups_landed_cost_estimate_ddp = True
        self.sale.partner_shipping_id = self.be_partner
        self.sale.ups_landed_cost_estimate_amount = 42.0
        self._add_estimate_line(self.sale)
        picking = self.sale.picking_ids[0]
        picking.move_ids.quantity = 10
        picking.number_of_packages = 1
        picking.partner_id = self.env["res.partner"].create(
            {"name": "Other Country", "country_id": self.env.ref("base.fr").id}
        )
        ups_request = UpsRequest(self.carrier)
        vals = ups_request._prepare_create_shipping(picking)
        shipment = vals["ShipmentRequest"]["Shipment"]
        self.assertNotIn("QuoteID", shipment)
        charges = shipment["PaymentInformation"]["ShipmentCharge"]
        self.assertTrue(any(c.get("Type") == "02" for c in charges))
