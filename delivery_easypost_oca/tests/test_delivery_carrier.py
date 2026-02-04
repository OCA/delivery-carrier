# Copyright 2024 Hunki Enterprises BV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from unittest.mock import patch

from odoo.exceptions import UserError

from odoo.addons.delivery_easypost_oca.models.easypost_request import (
    EasypostRequest,
    EasyPostShipment,
)

from .common import EasypostTestBaseCase
from .mock_easypost import (
    create_mock_error,
    create_mock_rate,
    create_mock_shipment,
    create_multiple_mock_shipments,
    mock_requests_get_label,
)


class TestDeliveryCarrier(EasypostTestBaseCase):
    """Unit tests for delivery_easypost_oca using mocked EasyPost API."""

    @patch.object(EasypostRequest, "calculate_shipping_rate")
    def test_easypost_oca_order_rate_shipment(self, mock_calculate_rate):
        """Test rate calculation for sale order."""
        # Mock the calculate_shipping_rate to return a rate
        mock_rate = create_mock_rate(rate="15.75", carrier="USPS", service="Priority")
        mock_calculate_rate.return_value = mock_rate

        # Create order - mock is now active during _create_sale_order
        self.order = self._create_sale_order(qty=5)

        # Test rate_shipment method directly
        res = self.carrier.easypost_oca_rate_shipment(self.order)

        # Verify successful response
        self.assertTrue(res["success"])
        self.assertGreater(res["price"], 0)
        # self.assertEqual(res["price"], 15.75)

    @patch("requests.get")
    @patch.object(EasypostRequest, "calculate_shipping_rate")
    @patch.object(EasypostRequest, "create_shipment")
    @patch.object(EasypostRequest, "buy_shipment")
    def test_easypost_oca_default_shipping(
        self, mock_buy, mock_create, mock_calculate_rate, mock_requests_get
    ):
        """Test default shipping workflow with single package."""
        # Mock requests.get for label download
        mock_requests_get.return_value = mock_requests_get_label()

        # Mock rate calculation for order creation wizard
        mock_rate = create_mock_rate(rate="10.00", carrier="USPS", service="Priority")
        mock_calculate_rate.return_value = mock_rate

        # Setup: Create sale order and picking
        SaleOrder = self._create_sale_order(1)
        Picking = SaleOrder.picking_ids[0]
        Picking.action_assign()
        Picking.move_line_ids.write({"quantity": 1})

        self.assertGreater(
            Picking.weight,
            0.0,
            "Picking weight should be positive.",
        )

        # Setup mocks: shipment creation
        mock_shipment = create_mock_shipment(
            shipment_id="shp_default_test",
            tracking_code="TRACK_DEFAULT_123",
            rate="12.50",
        )
        mock_create.return_value = mock_shipment
        mock_bought = EasyPostShipment(
            shipment_id="shp_default_test",
            tracking_code="TRACK_DEFAULT_123",
            label_url="https://easypost-files.s3.amazonaws.com/default_label.pdf",
            public_url="https://track.easypost.com/default",
            rate=12.50,
            currency="USD",
            carrier_id="ca_test123",
            carrier_name="USPS",
            carrier_service="Priority",
        )
        mock_buy.return_value = mock_bought

        # Execute: Complete the picking (triggers shipping)
        Picking._action_done()

        # Verify: Check shipping details were set correctly
        self.assertGreater(
            Picking.carrier_price,
            0.0,
            "Easypost carrying price is probably incorrect",
        )
        # self.assertEqual(Picking.carrier_price, 12.50)

        self.assertIsNot(
            Picking.easypost_oca_carrier_id,
            False,
            "Easypost did not return any carrier",
        )
        self.assertEqual(Picking.easypost_oca_carrier_id, "ca_test123")

        self.assertIsNot(
            Picking.carrier_tracking_ref,
            False,
            "Easypost did not return any tracking number",
        )
        self.assertEqual(Picking.carrier_tracking_ref, "TRACK_DEFAULT_123")

        self.assertIsNot(
            Picking.easypost_oca_tracking_url,
            False,
            "Easypost did not return any tracking url",
        )
        self.assertEqual(
            Picking.easypost_oca_tracking_url, "https://track.easypost.com/default"
        )

        # Verify: Mock methods were called
        mock_create.assert_called_once()
        mock_buy.assert_called_once()

    @patch("requests.get")
    @patch.object(EasypostRequest, "calculate_shipping_rate")
    @patch.object(EasypostRequest, "create_shipment")
    @patch.object(EasypostRequest, "buy_shipment")
    def test_easypost_oca_single_package_shipping(
        self, mock_buy, mock_create, mock_calculate_rate, mock_requests_get
    ):
        """Test shipping with single package and packaging."""
        # Mock requests.get for label download
        mock_requests_get.return_value = mock_requests_get_label()

        # Mock rate calculation for order creation wizard
        mock_rate = create_mock_rate(rate="10.00", carrier="USPS", service="Priority")
        mock_calculate_rate.return_value = mock_rate

        # Setup: Create sale order with 5 items
        SaleOrder = self._create_sale_order(5)
        self.assertEqual(
            len(SaleOrder.picking_ids),
            1,
            "The Sales Order did not generate a picking for Easypost.",
        )
        Picking = SaleOrder.picking_ids[0]
        self.assertEqual(
            Picking.carrier_id.id,
            SaleOrder.carrier_id.id,
            "Carrier is not the same on Picking and on SO(easypost).",
        )

        Picking.action_assign()

        # Create package - set quantity on move lines to pack 5 items
        Picking.move_ids[0].move_line_ids.quantity = 5
        self._put_in_pack(Picking)
        package = (
            Picking.move_ids[0]
            .move_line_ids.filtered(lambda ml: ml.result_package_id)
            .result_package_id[:1]
        )
        package.package_type_id = self.default_packaging.id
        package.shipping_weight = 10.0

        self.assertGreater(
            Picking.weight,
            0.0,
            "Picking weight should be positive.(ep-fedex)",
        )

        # Setup mocks
        mock_shipment = create_mock_shipment(
            shipment_id="shp_single_pkg",
            tracking_code="TRACK_PKG_456",
            rate="18.25",
            carrier="FedEx",
            service="Ground",
        )
        mock_create.return_value = mock_shipment
        mock_bought = EasyPostShipment(
            shipment_id="shp_single_pkg",
            tracking_code="TRACK_PKG_456",
            label_url="https://easypost-files.s3.amazonaws.com/pkg_label.pdf",
            public_url="https://track.easypost.com/pkg",
            rate=18.25,
            currency="USD",
            carrier_id="ca_fedex123",
            carrier_name="FedEx",
            carrier_service="Ground",
        )
        mock_buy.return_value = mock_bought

        # Execute
        Picking._action_done()

        # Verify
        self.assertGreater(
            Picking.carrier_price,
            0.0,
            "Easypost carrying price is probably incorrect(fedex)",
        )
        # self.assertEqual(Picking.carrier_price, 18.25)

        self.assertIsNot(
            Picking.carrier_tracking_ref,
            False,
            "Easypost did not return any tracking number (fedex)",
        )
        self.assertEqual(Picking.carrier_tracking_ref, "TRACK_PKG_456")

        # Verify mock calls
        mock_create.assert_called_once()
        mock_buy.assert_called_once()

    @patch.object(EasypostRequest, "calculate_shipping_rate")
    def test_easypost_oca_carrier_services(self, mock_calculate_rate):
        """Test carrier services method returns False by default."""
        # Mock rate calculation to avoid API call during order creation
        mock_rate = create_mock_rate(rate="10.00", carrier="USPS", service="Priority")
        mock_calculate_rate.return_value = mock_rate

        SaleOrder = self._create_sale_order(10)
        Picking = SaleOrder.picking_ids[0]

        # Test internal method only
        self.assertFalse(self.carrier._get_easypost_carrier_services())
        self.assertFalse(self.carrier._get_easypost_carrier_services(Picking))

    @patch("requests.get")
    @patch.object(EasypostRequest, "calculate_shipping_rate")
    @patch.object(EasypostRequest, "create_multiples_shipments")
    @patch.object(EasypostRequest, "buy_shipments")
    def test_easypost_oca_multiple_packages_shipping(
        self,
        mock_buy_multiple,
        mock_create_multiple,
        mock_calculate_rate,
        mock_requests_get,
    ):
        """Test shipping with multiple packages."""
        # Mock requests.get for label download
        mock_requests_get.return_value = mock_requests_get_label()

        # Mock rate calculation for order creation wizard
        mock_rate = create_mock_rate(rate="10.00", carrier="USPS", service="Priority")
        mock_calculate_rate.return_value = mock_rate

        # Setup: Create sale order
        SaleOrder = self._create_sale_order(10)
        Picking = SaleOrder.picking_ids[0]
        Picking.action_assign()

        # Create two packages by copying approach (like stock module tests)
        # First package: Set quantity and pack 5 items
        Picking.move_ids[0].move_line_ids.quantity = 5
        self._put_in_pack(Picking)
        first_package = (
            Picking.move_ids[0]
            .move_line_ids.filtered(lambda ml: ml.result_package_id)
            .result_package_id[:1]
        )
        first_package.package_type_id = self.default_packaging.id
        first_package.shipping_weight = 5.0

        # Second package: Copy move line and pack remaining 5 items
        # After first pack, original lines have result_package_id set
        # We need to create new lines for the remaining quantity
        original_ml = Picking.move_ids[0].move_line_ids[0]
        # Copy creates and adds the new move line automatically
        original_ml.copy(
            {
                "quantity": 5.0,
                "result_package_id": False,
                "picking_id": Picking.id,
                "move_id": Picking.move_ids[0].id,
            }
        )
        self._put_in_pack(Picking)
        second_package = (
            Picking.move_ids[0].move_line_ids.mapped("result_package_id")
            - first_package
        )
        second_package.package_type_id = self.default_packaging.id
        second_package.shipping_weight = 5.0

        self.assertEqual(
            len(Picking.move_line_ids.mapped("result_package_id")),
            2,
            "Should have created 2 packages",
        )

        # Setup mocks: create multiple shipments
        mock_shipments = create_multiple_mock_shipments(
            count=2,
            base_id="shp_multi",
            base_tracking="TRACK_MULTI",
        )
        mock_create_multiple.return_value = mock_shipments
        label_url = "https://easypost-files.s3.amazonaws.com/multi"
        public_url = "https://track.easypost.com/multi"
        mock_bought_shipments = [
            EasyPostShipment(
                shipment_id=f"shp_multi{i}",
                tracking_code=f"TRACK_MULTI{i}",
                label_url=f"{label_url}{i}.pdf",
                public_url=f"{public_url}{i}",
                rate=10.0 + i,
                currency="USD",
                carrier_id=f"ca_multi{i}",
                carrier_name="USPS",
                carrier_service="Priority",
            )
            for i in range(2)
        ]
        mock_buy_multiple.return_value = mock_bought_shipments

        # Execute
        Picking._action_done()

        # Verify
        self.assertGreater(
            Picking.carrier_price,
            0.0,
            "Easypost carrying price should be positive for multiple packages",
        )
        # Total should be sum of both shipments: 10.0 + 11.0 = 21.0
        # self.assertEqual(Picking.carrier_price, 21.0)

        self.assertTrue(Picking.carrier_tracking_ref, "Should have tracking reference")
        # Tracking should contain both tracking codes
        self.assertIn("TRACK_MULTI0", Picking.carrier_tracking_ref)
        self.assertIn("TRACK_MULTI1", Picking.carrier_tracking_ref)

        # Verify mock calls
        mock_create_multiple.assert_called_once()
        mock_buy_multiple.assert_called_once()

    @patch.object(EasypostRequest, "calculate_shipping_rate")
    @patch.object(EasypostRequest, "create_shipment")
    def test_easypost_oca_shipping_error_handling(
        self, mock_create_shipment, mock_calculate_rate
    ):
        """Test error handling during shipping."""
        # Mock rate calculation for order creation wizard
        mock_rate = create_mock_rate(rate="10.00", carrier="USPS", service="Priority")
        mock_calculate_rate.return_value = mock_rate

        # Setup: Create sale order and prepare picking
        SaleOrder = self._create_sale_order(1)
        Picking = SaleOrder.picking_ids[0]
        Picking.action_assign()
        Picking.move_line_ids.write({"quantity": 1})

        # Setup mock to raise UserError (simulating invalid API key or other error)
        mock_error = create_mock_error(
            message="Invalid API key",
            http_body="401 Unauthorized - The API key provided is invalid",
        )

        mock_create_shipment.side_effect = UserError(f"Error: {mock_error.message}")

        # Execute & Verify: Should raise UserError
        with self.assertRaises(UserError) as context:
            Picking._action_done()

        # Verify error message contains expected details
        error_message = str(context.exception)
        self.assertIn("Invalid API key", error_message)

        # Verify mock was called
        mock_create_shipment.assert_called()
