from unittest.mock import Mock, patch

from odoo.exceptions import UserError

from odoo.addons.delivery_easypost_oca.models.easypost_request import EasypostRequest

from .common import EasypostTestBaseCase


class TestEasypostRequest(EasypostTestBaseCase):
    def setUp(self):
        super().setUp()
        self.easypost_request = EasypostRequest(self.carrier)

    @patch("easypost.Shipment")
    def test_create_shipment(self, mock_shipment):
        # Prepare test data
        mock_response = Mock()
        mock_response.id = "shp_123"
        mock_shipment.create.return_value = mock_response

        from_address = {
            "name": "EasyPost",
            "street1": "118 2nd Street",
            "street2": "4th Floor",
            "city": "San Francisco",
            "state": "CA",
            "zip": "94105",
            "country": "US",
            "phone": "415-456-7890",
        }
        to_address = {
            "name": "Dr. Steve Brule",
            "street1": "179 N Harbor Dr",
            "city": "Redondo Beach",
            "state": "CA",
            "zip": "90277",
            "country": "US",
            "phone": "310-808-5243",
        }
        parcel = {"weight": 17.5}

        # Execute test
        result = self.easypost_request.create_shipment(
            from_address=from_address, to_address=to_address, parcel=parcel
        )

        # Verify results
        self.assertEqual(result.id, "shp_123")
        mock_shipment.create.assert_called_once_with(
            from_address=from_address,
            to_address=to_address,
            parcel=parcel,
            options={},
            reference=None,
            carrier_accounts=[],
        )

    @patch("easypost.Shipment")
    def test_create_shipment_error(self, mock_shipment):
        # Simulate API error
        mock_shipment.create.side_effect = Exception("API Error")

        # Test error handling
        with self.assertRaises(UserError):
            self.easypost_request.create_shipment(
                from_address={}, to_address={}, parcel={}
            )

    @patch("easypost.Shipment")
    def test_buy_shipment(self, mock_shipment):
        # Prepare mock response
        mock_response = Mock()
        mock_response.id = "shp_123"
        mock_response.tracking_code = "TRACK123"
        mock_response.postage_label.label_url = "http://label.url"
        mock_response.tracker.public_url = "http://track.url"
        mock_response.selected_rate.rate = "10.0"
        mock_response.selected_rate.currency = "USD"
        mock_response.selected_rate.carrier_account_id = "ca_123"
        mock_response.selected_rate.carrier = "USPS"
        mock_response.selected_rate.service = "Priority"

        # Setup mock shipment
        mock_shipment_obj = Mock()
        mock_shipment_obj.buy.return_value = mock_response
        mock_shipment_obj.lowest_rate.return_value = mock_response.selected_rate

        # Execute test
        result = self.easypost_request.buy_shipment(mock_shipment_obj)

        # Verify results
        self.assertEqual(result.shipment_id, "shp_123")
        self.assertEqual(result.tracking_code, "TRACK123")
        self.assertEqual(result.label_url, "http://label.url")
        self.assertEqual(result.public_url, "http://track.url")
        self.assertEqual(result.rate, 10.0)
        self.assertEqual(result.currency, "USD")
        self.assertEqual(result.carrier_id, "ca_123")
        self.assertEqual(result.carrier_name, "USPS")
        self.assertEqual(result.carrier_service, "Priority")
