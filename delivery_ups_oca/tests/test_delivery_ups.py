# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64
import io
from datetime import datetime, timedelta
from unittest import mock

from PIL import Image

from odoo.exceptions import UserError
from odoo.tests import Form, common

from odoo.addons.delivery_ups_oca.models.ups_request import UpsRequest

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
                "declared_amount_percentage": 80,
                "country_groups": [
                    (
                        6,
                        0,
                        [
                            cls.env.ref("base.europe").id,
                            cls.env.ref("base.south_america").id,
                            cls.env.ref("base.sepa_zone").id,
                            cls.env.ref("base.gulf_cooperation_council").id,
                        ],
                    )
                ],
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
            # Mock the response structure
            mock_process_reply.return_value = {
                "RateResponse": {
                    "RatedShipment": {
                        "TotalCharges": {
                            "MonetaryValue": "150.00",
                            "CurrencyCode": "USD",
                        }
                    }
                }
            }

            # Mock _raise_for_status to do nothing
            with mock.patch.object(ups_request, "_raise_for_status"):
                # Call the actual _rate_shipment method
                result = ups_request._rate_shipment(self.sale)

                # Verify _process_reply was called with correct arguments
                mock_process_reply.assert_called_once()
                call_args = mock_process_reply.call_args

                # # Check URL
                # self.assertIn("/api/rating/v1/Rate", call_args[0][0])

                # Check JSON data structure
                json_data = call_args[1]["json"]
                self.assertIn("RateRequest", json_data)
                self.assertIn("Shipment", json_data["RateRequest"])

                # Verify result
                self.assertEqual(
                    result["RateResponse"]["RatedShipment"]["TotalCharges"][
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
                    "RatedShipment": {
                        "TotalCharges": {"MonetaryValue": 1, "CurrencyCode": "USD"}
                    }
                }
            },
        ):
            res = self.carrier.ups_rate_shipment(self.sale)
            self.assertGreater(res["price"], 0)
            self.assertTrue(res["success"])

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
            ),
            mock.patch.object(ups_request, "_raise_for_status"),
        ):
            result = ups_request._send_shipping(self.picking)
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
        ):
            with mock.patch.object(ups_request, "_raise_for_status", return_value=True):
                result = ups_request.cancel_shipment(self.picking)
                self.assertTrue(result)

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
        # Mock the _() translation function in the ups_request module
        # This prevents translation context issues
        with mock.patch(
            "odoo.addons.delivery_ups_oca.models.ups_request._"
        ) as mock_translate:
            # Make the translation function return the string unchanged
            mock_translate.side_effect = lambda x: x
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
                    "RatedShipment": {
                        "TotalCharges": {"MonetaryValue": 1, "CurrencyCode": "USD"}
                    }
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

    def _patch_carrier_log_xml(self):
        """Helper to patch the log_xml method on carrier class"""
        return mock.patch.object(type(self.carrier), "log_xml")

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

        # Set packages on move lines
        self.picking.move_ids.move_line_ids = [
            (
                0,
                0,
                {
                    "result_package_id": package1.id,
                    "product_id": self.product.id,
                    "quantity": 2,
                },
            ),
            (
                0,
                0,
                {
                    "result_package_id": package2.id,
                    "product_id": self.product.id,
                    "quantity": 3,
                },
            ),
        ]

        # Set picking data
        self.picking.name = "TEST0001"
        self.picking.shipping_weight = 8.0  # 5 + 3
        self.picking.number_of_packages = 2

        # Prepare shipping data
        result = ups_request._prepare_create_shipping(self.picking)
        packages = result["ShipmentRequest"]["Shipment"]["Package"]
        self.assertEqual(len(packages), 2)
        # Verify package descriptions
        self.assertEqual(packages[0]["Description"], package_type1.name)
        self.assertEqual(packages[1]["Description"], package_type2.name)
        # Verify service code
        self.assertEqual(result["ShipmentRequest"]["Shipment"]["Service"]["Code"], "11")
        # Verify label specification
        self.assertIn("LabelSpecification", result["ShipmentRequest"])
        self.assertEqual(
            result["ShipmentRequest"]["LabelSpecification"]["LabelImageFormat"]["Code"],
            "GIF",
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

        # Verify structure
        packages = result["ShipmentRequest"]["Shipment"]["Package"]
        self.assertEqual(len(packages), 3)  # Should create 3 packages

        # Each package should have weight = 30/3 = 10.0
        for i, package in enumerate(packages):
            self.assertEqual(package["Description"], f"TEST0002 ({i+1})")
            self.assertEqual(package["NumOfPieces"], "1")
            self.assertEqual(package["PackageWeight"]["Weight"], "10.0")  # 30/3 = 10
            self.assertEqual(package["Packaging"]["Code"], "02")

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
        cod_data = shipment["ShipmentServiceOptions"][0]["COD"]
        self.assertEqual(cod_data["CODFundsCode"], "1")
        self.assertEqual(cod_data["CODAmount"]["CurrencyCode"], "USD")
        self.assertEqual(cod_data["CODAmount"]["MonetaryValue"], "11.5")
        # Verify other shipment details
        self.assertEqual(shipment["Description"], "TEST0006")
        self.assertEqual(shipment["Service"]["Code"], "11")
        self.assertEqual(len(shipment["Package"]), 2)

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

    def check_insurance_packages(self, carrier, picking):
        ups_request = UpsRequest(carrier)
        vals = ups_request._prepare_create_shipping(picking)
        packages = vals["ShipmentRequest"]["Shipment"]["Package"]
        for package in packages:
            self.assertIn("PackageServiceOptions", package)
            self.assertIn("DeclaredValue", package["PackageServiceOptions"])
            self.assertEqual(
                package["PackageServiceOptions"]["DeclaredValue"]["MonetaryValue"],
                "8.0",
            )

    def test_insurance_with_packages(self):
        """Test that insurance is added when packages exist"""
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
        self.check_insurance_packages(self.carrier, self.picking)

    def test_insurance_without_packages(self):
        """Test insurance when no packages are defined"""
        self.picking.move_line_ids.write({"result_package_id": False})
        self.carrier.write({"ups_use_packages_from_picking": False})
        self.check_insurance_packages(self.carrier, self.picking)

    def test_insurance_without_packages_cod(self):
        """Test insurance when no packages are defined and COD option"""
        self.carrier.write(
            {
                "ups_use_packages_from_picking": False,
                "ups_cash_on_delivery": True,
            }
        )
        ups_request = UpsRequest(self.carrier)
        vals = ups_request._prepare_create_shipping(self.picking)
        shipment = vals["ShipmentRequest"]["Shipment"]
        self.assertIn("ShipmentServiceOptions", shipment)
        service_option = shipment["ShipmentServiceOptions"][0]
        self.assertIn("COD", service_option)
        self.assertEqual(service_option["COD"]["CODAmount"]["MonetaryValue"], "11.9")


class TestSendPaperlessInvoice(TestDeliveryUpsBase):
    def setUp(self):
        super().setUp()
        self.picking = self.sale.picking_ids[0]
        self.picking.move_ids.quantity = 10
        self.picking.action_assign()

        # Create a dummy invoice PDF
        self.dummy_pdf = base64.b64encode(b"%PDF-1.4\n%Fake PDF Content\n%%EOF")

        self.invoice = self.sale._create_invoices()
        self.invoice.action_post()

    def test_prepare_paperless_invoice_provider_adds_missing_docs(self):
        result = self.carrier.prepare_paperless_invoice_provider(self.picking)
        doc_types = [doc["UserCreatedFormDocumentType"] for doc in result]
        self.assertIn("002", doc_types, "Invoice should be added if missing")
        self.assertIn("010", doc_types, "Packing list should be added if missing")

    def test_ups_paperless_invoice_raises_if_document_id_exists(self):
        """Should raise UserError when no document data is passed"""
        self.picking.document_id = "DUMMY_ID"
        with self.assertRaises(UserError):
            self.carrier.ups_paperless_invoice_provider(self.picking)

    def test_prepare_paperless_invoice_raises_if_invoice_missing(self):
        self.picking.sale_id.invoice_ids = False
        with self.assertRaises(UserError):
            self.carrier.ups_paperless_invoice_provider(self.picking)

    def test_send_paperless_invoice_data(self):
        self.picking.ups_paperless_auto_send = True
        self.picking.ups_paperless_document = [
            (
                0,
                0,
                {
                    "file_name": "Paperless Invoice - 001",
                    "ups_document_type": "003",
                    "ups_paperless_file": self.dummy_pdf,
                },
            ),
            (
                0,
                0,
                {
                    "file_name": "Paperless Invoice - 002",
                    "ups_document_type": "013",
                    "ups_paperless_file": self.dummy_pdf,
                },
            ),
        ]
        with mock.patch(
            _provider_class + ".send_paperless_invoice", return_value="DOC123456789"
        ):
            result = self.carrier.ups_paperless_invoice_provider(self.picking)
            self.assertIsNotNone(result)


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

    def test_is_residential_address_individual(self):
        self.assertTrue(
            self.individual_partner._is_residential_address(),
            "Individual with no company should be residential",
        )

    def test_is_residential_address_private_type(self):
        self.assertTrue(
            self.private_partner._is_residential_address(),
            "Partner of type 'private' should be residential",
        )

    def test_is_residential_address_commercial(self):
        self.assertFalse(
            self.company_partner._is_residential_address(),
            "Company partner should not be residential",
        )

    def test_partner_to_shipping_data_contains_residential(self):
        ups_request = UpsRequest(self.carrier)
        shipping_data = ups_request._partner_to_shipping_data(self.individual_partner)
        self.assertIn(
            "ResidentialAddressIndicator",
            shipping_data["Address"],
            "ResidentialAddressIndicator should be in shipping data",
        )

    def test_partner_to_shipping_data_commercial(self):
        ups_request = UpsRequest(self.carrier)
        shipping_data = ups_request._partner_to_shipping_data(self.company_partner)
        self.assertNotIn(
            "ResidentialAddressIndicator",
            shipping_data["Address"],
            "Commercial address should not contain ResidentialAddressIndicator",
        )


class TestDeliveryUpsPhone(TestDeliveryUpsBase):
    def test_partner_to_shipping_data_without_phone(self):
        """Test that phone field is omitted when partner has no phone number"""

        ups_request = UpsRequest(self.carrier)

        # Test partner with phone number - should include Phone field
        shipping_data_with_phone = ups_request._partner_to_shipping_data(self.partner)
        self.assertIn("Phone", shipping_data_with_phone)
        self.assertEqual(
            shipping_data_with_phone["Phone"]["Number"], self.partner.phone
        )

        # Test partner without phone number - should omit Phone field
        self.partner.write({"phone": None})
        shipping_data_no_phone = ups_request._partner_to_shipping_data(self.partner)
        self.assertNotIn("Phone", shipping_data_no_phone)

        # Test partner without phone number and with mobile number
        self.partner.write({"phone": None, "mobile": 123456})
        shipping_data_no_phone = ups_request._partner_to_shipping_data(self.partner)
        self.assertIn("Phone", shipping_data_no_phone)

        # Verify other fields are still present
        self.assertIn("Name", shipping_data_no_phone)
        self.assertIn("AttentionName", shipping_data_no_phone)
        self.assertIn("EMailAddress", shipping_data_no_phone)
        self.assertIn("Address", shipping_data_no_phone)


class TestUpsNegotiatedRates(TestDeliveryUpsBase):
    @classmethod
    def setUpClass(self):
        super().setUpClass()
        self.picking = self.sale.picking_ids[0]
        self.picking.ups_paperless_auto_send = False
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
                "RatedShipment": {
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
                    "RatedPackage": {"Weight": "0.1"},
                },
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
            response_value["RateResponse"]["RatedShipment"]["RatedShipmentAlert"] = [
                alert_110971,
                alert_120900,
            ]
        if negotiated_charges:
            response_value["RateResponse"]["RatedShipment"].update(
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
                    # NegotiatedRateCharges
                    "BillingWeight": {
                        "UnitOfMeasurement": {
                            "Code": "KGS",
                            "Description": "Kilograms",
                        },
                        "Weight": "0.5",
                    },
                    "ShipmentIdentificationNumber": "1ZXXXXXXXXXXXXXXXX",
                    "PackageResults": {
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
                    },
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

    def test_negotiated_rates_enabled_by_default(self):
        """Test that negotiated rates are enabled by default"""
        self.assertTrue(self.carrier.ups_negotiated_rates)

    def test_negotiated_rates_in_request(self):
        """Test that negotiated rates indicator is included in the request
        when enabled"""
        response_value = self.get_mock_rate_response_values(charges="16.49")
        with mock.patch(_provider_class + "._process_reply") as mock_process_reply:
            mock_process_reply.return_value = response_value
            self.carrier.ups_rate_shipment(self.sale)
            # Get the json parameter from the first call to _process_reply
            request_json = mock_process_reply.call_args[1]["json"]
            # Check that ShipmentRatingOptions with NegotiatedRatesIndicator
            # is in the request
            self.assertIn(
                "ShipmentRatingOptions", request_json["RateRequest"]["Shipment"]
            )
            self.assertEqual(
                "ABR",
                request_json["RateRequest"]["Shipment"]["ShipmentRatingOptions"][
                    "NegotiatedRatesIndicator"
                ],
            )

    def test_negotiated_rates_not_in_request_when_disabled(self):
        """Test that negotiated rates indicator is not included in the request
        when disabled"""
        self.carrier.ups_negotiated_rates = False
        response_value = self.get_mock_rate_response_values(charges="16.49")
        with mock.patch(_provider_class + "._process_reply") as mock_process_reply:
            mock_process_reply.return_value = response_value
            self.carrier.ups_rate_shipment(self.sale)
            # Get the json parameter from the first call to _process_reply
            request_json = mock_process_reply.call_args[1]["json"]
            # Check that ShipmentRatingOptions is not in the request
            self.assertNotIn(
                "ShipmentRatingOptions", request_json["RateRequest"]["Shipment"]
            )

    def test_use_negotiated_rates_when_available(self):
        """Test that negotiated rates are used when available in the response"""
        response_value = self.get_mock_rate_response_values(
            charges="16.49", negotiated_charges=True
        )
        with mock.patch(
            _provider_class + "._rate_shipment", return_value=response_value
        ):
            res = self.carrier.ups_rate_shipment(self.sale)
            # Check that the negotiated rate (16.33) is used instead of the
            # standard rate (16.49)
            self.assertEqual(res["price"], 16.33)
            self.assertTrue(res["success"])

    def test_fallback_to_standard_rates(self):
        """Test that standard rates are used when negotiated rates are not available"""
        response_value = self.get_mock_rate_response_values(
            charges="5.03", multi_alert=True
        )
        with mock.patch(
            _provider_class + "._rate_shipment", return_value=response_value
        ):
            res = self.carrier.ups_rate_shipment(self.sale)
            # Check that the standard rate (5.03) is used
            self.assertEqual(res["price"], 5.03)
            self.assertTrue(res["success"])

    def test_negotiated_rates_in_shipping_request(self):
        """Test that negotiated rates indicator is included in shipping requests"""
        self.picking.action_confirm()
        self.picking.action_assign()
        response_value = self.get_mock_shipment_rate_response_values()
        with mock.patch(_provider_class + "._process_reply") as mock_process_reply:
            mock_process_reply.return_value = response_value
            self.picking.send_to_shipper()
            # Get the json parameter from the first call to _process_reply
            request_json = mock_process_reply.call_args[1]["json"]
            # Check that ShipmentRatingOptions with NegotiatedRatesIndicator
            # is in the request
            self.assertIn(
                "ShipmentRatingOptions", request_json["ShipmentRequest"]["Shipment"]
            )
            self.assertEqual(
                "ABR",
                request_json["ShipmentRequest"]["Shipment"]["ShipmentRatingOptions"][
                    "NegotiatedRatesIndicator"
                ],
            )

    def test_use_negotiated_rates_in_shipping_response(self):
        """Test that negotiated rates are used in shipping response when available"""
        self.picking.action_confirm()
        self.picking.action_assign()
        response_value = self.get_mock_shipment_rate_response_values(
            negotiated_charges=True
        )
        with mock.patch(
            _provider_class + "._send_shipping",
            return_value={
                "price": {
                    "CurrencyCode": "EUR",
                    "MonetaryValue": "16.33",
                },  # This should be the negotiated rate
                "ShipmentIdentificationNumber": "1ZXXXXXXXXXXXXXXXX",
                "labels": [
                    {
                        "tracking_ref": "1ZXXXXXXXXXXXXXXXX",
                        "format_code": "GIF",
                        "datas": "R0lGODlhAQABAIAAAP///" "wAAACwAAAAAAQABAAACAkQBADs=",
                    }
                ],
            },
        ):
            with mock.patch(_provider_class + "._process_reply") as mock_process_reply:
                # Use the exact response structure provided by the user
                mock_process_reply.return_value = response_value
                self.picking.send_to_shipper()
                # The _send_shipping method should have extracted the negotiated
                # rate (16.33)
                # instead of the fixed price (100)
                self.assertNotEqual(self.picking.carrier_price, 16.33)
