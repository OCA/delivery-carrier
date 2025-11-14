from unittest.mock import Mock, patch

from odoo.exceptions import UserError

from odoo.addons.delivery_easypost_oca.models.easypost_request import EasypostRequest

from .common import EasypostTestBaseCase


class TestEasypostRequest(EasypostTestBaseCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.easypost_request = EasypostRequest(cls.carrier)

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

        # Execute test - pass as shipment dictionary
        shipment_data = {
            "from_address": from_address,
            "to_address": to_address,
            "parcel": parcel,
        }
        result = self.easypost_request.create_shipment(shipment_data)

        # Verify results
        self.assertEqual(result.id, "shp_123")
        mock_shipment.create.assert_called_once_with(
            from_address=from_address,
            to_address=to_address,
            parcel=parcel,
        )

    # @patch("easypost.Shipment")
    # def test_create_shipment_error(self, mock_shipment):
    #     # Simulate API error
    #     mock_shipment.create.side_effect = Exception("API Error")

    #     # Test error handling
    #     shipment_data = {
    #         "from_address": {},
    #         "to_address": {},
    #         "parcel": {},
    #     }
    #     # Verify that error is logged and UserError is raised
    #     with self.assertLogs(
    #         "odoo.addons.delivery_easypost_oca.models.easypost_request", level="ERROR"
    #     ) as log:
    #         with self.assertRaises(UserError):
    #             self.easypost_request.create_shipment(shipment_data)
    #         # Verify error was logged correctly
    #         self.assertIn("Failed to create shipment: API Error", log.output[0])

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

    @patch("easypost.EndShipper")
    def test_create_end_shipper(self, mock_end_shipper):
        # Prepare mock response
        mock_response = Mock()
        mock_response.id = "es_123"
        mock_end_shipper.create.return_value = mock_response

        # Test address
        address = {
            "name": "EasyPost",
            "street1": "118 2nd Street",
            "city": "San Francisco",
            "state": "CA",
            "zip": "94105",
            "country": "US",
        }

        # Execute test
        result = self.easypost_request.create_end_shipper(address)

        # Verify results
        self.assertEqual(result.id, "es_123")
        # Verify street2 was set to street1 as default
        expected_address = address.copy()
        expected_address["street2"] = address["street1"]
        mock_end_shipper.create.assert_called_once_with(**expected_address)

    # @patch("easypost.EndShipper")
    # def test_create_end_shipper_error(self, mock_end_shipper):
    #     # Simulate API error
    #     mock_end_shipper.create.side_effect = Exception("API Error")

    #     # Test error handling
    #     address = {"street1": "123 Main St"}
    #     with self.assertRaises(UserError):
    #         self.easypost_request.create_end_shipper(address)

    @patch("easypost.EndShipper")
    def test_get_end_shipper_id_usps(self, mock_end_shipper):
        # Mock end shipper list
        mock_end_shipper_obj = Mock()
        mock_end_shipper_obj.get.return_value = "es_existing"
        mock_end_shipper.all.return_value = {"end_shippers": [mock_end_shipper_obj]}

        # Create mock shipment with USPS carrier
        mock_shipment = Mock()
        mock_shipment.from_address = {
            "name": "Test",
            "street1": "123 Main St",
            "city": "City",
            "state": "CA",
            "zip": "12345",
            "country": "US",
        }

        # Create mock rate with USPS carrier
        selected_rate = {"carrier": "USPS"}

        # Execute test
        result = self.easypost_request._get_end_shipper_id(selected_rate, mock_shipment)

        # Verify results
        self.assertEqual(result, "es_existing")
        mock_end_shipper.all.assert_called_once_with(page_size=1)

    @patch("easypost.EndShipper")
    def test_get_end_shipper_id_ups(self, mock_end_shipper):
        # Mock end shipper list
        mock_end_shipper_obj = Mock()
        mock_end_shipper_obj.get.return_value = "es_ups"
        mock_end_shipper.all.return_value = {"end_shippers": [mock_end_shipper_obj]}

        # Create mock shipment with UPS carrier
        mock_shipment = Mock()
        mock_shipment.from_address = {
            "name": "Test",
            "street1": "123 Main St",
            "city": "City",
            "state": "CA",
            "zip": "12345",
            "country": "US",
        }

        # Create mock rate with UPS carrier
        selected_rate = {"carrier": "UPS"}

        # Execute test
        result = self.easypost_request._get_end_shipper_id(selected_rate, mock_shipment)

        # Verify results
        self.assertEqual(result, "es_ups")

    @patch("easypost.EndShipper")
    def test_get_end_shipper_id_other_carrier(self, mock_end_shipper):
        # Create mock shipment
        mock_shipment = Mock()
        selected_rate = {"carrier": "FedEx"}

        # Execute test
        result = self.easypost_request._get_end_shipper_id(selected_rate, mock_shipment)

        # Verify results - should return None for non-USPS/UPS carriers
        self.assertIsNone(result)
        # EndShipper.all should not be called for other carriers
        mock_end_shipper.all.assert_not_called()

    @patch("easypost.EndShipper")
    def test_get_end_shipper_id_creates_new_when_empty(self, mock_end_shipper):
        # Mock empty end shipper list
        mock_end_shipper.all.return_value = {"end_shippers": []}

        # Mock create response
        mock_created = Mock()
        mock_created.get.return_value = "es_new"
        mock_end_shipper.create.return_value = mock_created

        # Create mock shipment
        mock_shipment = Mock()
        mock_shipment.from_address = {
            "name": "Test",
            "street1": "123 Main St",
            "city": "City",
            "state": "CA",
            "zip": "12345",
            "country": "US",
        }

        selected_rate = {"carrier": "USPS"}

        # Execute test
        result = self.easypost_request._get_end_shipper_id(selected_rate, mock_shipment)

        # Verify create was called
        self.assertEqual(result, "es_new")
        mock_end_shipper.create.assert_called_once()

    @patch("easypost.batch")
    def test_create_batch(self, mock_batch):
        # Prepare mock response
        mock_response = Mock()
        mock_response.id = "batch_123"
        mock_batch.create.return_value = mock_response

        # Mock shipments
        shipments = [Mock(), Mock()]

        # Execute test
        result = self.easypost_request.create_batch(shipments)

        # Verify results
        self.assertEqual(result.id, "batch_123")
        mock_batch.create.assert_called_once_with(shipments=shipments)

    @patch("easypost.batch")
    def test_create_batch_error(self, mock_batch):
        # Simulate API error
        mock_batch.create.side_effect = Exception("Batch creation failed")

        # Execute test
        with self.assertRaises(UserError):
            self.easypost_request.create_batch([])

    @patch("easypost.batch")
    def test_buy_batch(self, mock_batch):
        # Prepare mock response
        mock_response = Mock()
        mock_response.id = "batch_123"
        mock_response.state = "purchased"
        mock_batch.Buy.return_value = mock_response

        # Execute test
        result = self.easypost_request.buy_batch("batch_123")

        # Verify results
        self.assertEqual(result.id, "batch_123")
        self.assertEqual(result.state, "purchased")
        mock_batch.Buy.assert_called_once_with(id="batch_123")

    @patch("easypost.batch")
    def test_buy_batch_error(self, mock_batch):
        # Simulate API error
        mock_batch.Buy.side_effect = Exception("Batch purchase failed")

        # Execute test
        with self.assertRaises(UserError):
            self.easypost_request.buy_batch("batch_123")

    @patch("easypost.Shipment")
    def test_create_multiples_shipments(self, mock_shipment):
        # Prepare mock responses
        mock_response1 = Mock()
        mock_response1.id = "shp_1"
        mock_response2 = Mock()
        mock_response2.id = "shp_2"

        mock_shipment.create.side_effect = [mock_response1, mock_response2]

        # Prepare shipment data
        shipments = [
            {"from_address": {}, "to_address": {}, "parcel": {}},
            {"from_address": {}, "to_address": {}, "parcel": {}},
        ]

        # Execute test
        result = self.easypost_request.create_multiples_shipments(shipments)

        # Verify results
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].id, "shp_1")
        self.assertEqual(result[1].id, "shp_2")

    @patch("easypost.Shipment")
    def test_create_multiples_shipments_with_error(self, mock_shipment):
        # First succeeds, second fails
        mock_response1 = Mock()
        mock_response1.id = "shp_1"
        mock_shipment.create.side_effect = [
            mock_response1,
            Exception("Failed to create"),
        ]

        # Prepare shipment data
        shipments = [
            {"from_address": {}, "to_address": {}, "parcel": {}},
            {"from_address": {}, "to_address": {}, "parcel": {}},
        ]

        # Execute test with logging
        with self.assertLogs(
            "odoo.addons.delivery_easypost_oca.models.easypost_request", level="ERROR"
        ):
            result = self.easypost_request.create_multiples_shipments(shipments)

        # Should only have one successful shipment
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].id, "shp_1")

    @patch("easypost.Shipment")
    def test_retrieve_shipment(self, mock_shipment):
        # Prepare mock response
        mock_response = Mock()
        mock_response.id = "shp_123"
        mock_response.tracking_code = "TRACK123"
        mock_shipment.retrieve.return_value = mock_response

        # Execute test
        result = self.easypost_request.retrieve_shipment("shp_123")

        # Verify results
        self.assertEqual(result.id, "shp_123")
        self.assertEqual(result.tracking_code, "TRACK123")
        mock_shipment.retrieve.assert_called_once_with(id="shp_123")

    # @patch("easypost.Shipment")
    # def test_retrieve_shipment_error(self, mock_shipment):
    #     # Simulate API error
    #     mock_shipment.retrieve.side_effect = Exception("Shipment not found")

    #     # Execute test
    #     with self.assertRaises(UserError):
    #         self.easypost_request.retrieve_shipment("shp_invalid")

    @patch("easypost.beta.CarrierMetadata")
    def test_retrieve_carrier_metadata(self, mock_metadata):
        # Prepare mock response
        mock_response = Mock()
        mock_response.carriers = [{"name": "USPS"}, {"name": "FedEx"}]
        mock_metadata.retrieve_carrier_metadata.return_value = mock_response

        # Execute test
        result = self.easypost_request.retrieve_carrier_metadata()

        # Verify results
        self.assertEqual(len(result.carriers), 2)
        mock_metadata.retrieve_carrier_metadata.assert_called_once()

    # @patch("easypost.beta.CarrierMetadata")
    # def test_retrieve_carrier_metadata_error(self, mock_metadata):
    #     # Simulate API error
    #     mock_metadata.retrieve_carrier_metadata.side_effect = Exception(
    #         "Metadata retrieval failed"
    #     )

    #     # Execute test
    #     with self.assertRaises(UserError):
    #         self.easypost_request.retrieve_carrier_metadata()

    @patch("easypost.CarrierAccount")
    def test_retrieve_all_carrier_accounts(self, mock_carrier_account):
        # Prepare mock response
        mock_response = [
            {"id": "ca_1", "type": "USPS"},
            {"id": "ca_2", "type": "FedEx"},
        ]
        mock_carrier_account.all.return_value = mock_response

        # Execute test
        result = self.easypost_request.retrieve_all_carrier_accounts()

        # Verify results
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["id"], "ca_1")
        self.assertEqual(result[1]["id"], "ca_2")
        mock_carrier_account.all.assert_called_once()

    # @patch("easypost.CarrierAccount")
    # def test_retrieve_all_carrier_accounts_error(self, mock_carrier_account):
    #     # Simulate API error
    #     mock_carrier_account.all.side_effect = Exception(
    #         "Failed to retrieve accounts"
    #     )

    #     # Execute test
    #     with self.assertRaises(UserError):
    #         self.easypost_request.retrieve_all_carrier_accounts()
