# Copyright 2024 Binhex
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

"""
Mock utilities for EasyPost API testing.

This module provides reusable mock objects and fixtures for testing
the delivery_easypost_oca module without making real API calls.

All mock structures are based on real EasyPost API responses to ensure accuracy.
"""

from unittest.mock import Mock

# =============================================================================
# MOCK DATA FIXTURES (Based on real EasyPost API responses)
# =============================================================================

MOCK_ADDRESS_FROM = {
    "name": "My Company (San Francisco)",
    "company": "My Company (San Francisco)",
    "street1": "250 Executive Park Blvd, Suite 3400",
    "street2": None,
    "city": "San Francisco",
    "state": "CA",
    "zip": "94134",
    "country": "US",
    "phone": "16505550111",
    "email": "info@yourcompany.com",
}

MOCK_ADDRESS_TO = {
    "name": "DECO ADDICT",
    "company": "DECO ADDICT",
    "street1": "77 SANTA BARBARA RD",
    "street2": None,
    "city": "PLEASANT HILL",
    "state": "CA",
    "zip": "94523-4215",
    "country": "US",
    "phone": "6039963829",
    "email": "DECO.ADDICT82@EXAMPLE.COM",
}

MOCK_PARCEL_DATA = {
    "length": None,
    "width": None,
    "height": None,
    "weight": 0.5,  # lbs
    "predefined_package": None,
}

MOCK_OPTIONS = {
    "currency": "USD",
    "date_advance": 0,
    "label_format": "PDF",
    "payment": {"type": "SENDER"},
    "print_custom": [{"value": "WH/OUT/00017"}],
    "print_custom_1": "WH/OUT/00017",
}


# =============================================================================
# MOCK RESPONSE CLASSES (Structured like real EasyPost API objects)
# =============================================================================


class MockEasypostTrackingLocation:
    """Mock object for EasyPost TrackingLocation."""

    def __init__(self, city=None, state=None, zip_code=None, country=None):
        self.city = city
        self.state = state
        self.zip = zip_code
        self.country = country
        self.object = "TrackingLocation"


class MockEasypostTrackingDetail:
    """Mock object for EasyPost TrackingDetail."""

    def __init__(
        self,
        datetime_str=None,
        message="Delivered",
        status="delivered",
        status_detail="arrived_at_destination",
        tracking_location=None,
    ):
        self.datetime = datetime_str or "2025-10-16T17:07:08Z"
        self.message = message
        self.status = status
        self.status_detail = status_detail
        self.tracking_location = tracking_location or MockEasypostTrackingLocation(
            city="CHARLESTON", state="SC", zip_code="29407"
        )
        self.carrier_code = ""
        self.description = ""
        self.est_delivery_date = None
        self.object = "TrackingDetail"
        self.source = "USPS"


class MockEasypostCarrierDetail:
    """Mock object for EasyPost CarrierDetail."""

    def __init__(
        self,
        service="First-Class Package Service",
        origin_location="HOUSTON TX, 77001",
        destination_location="CHARLESTON SC, 29401",
    ):
        self.service = service
        self.origin_location = origin_location
        self.destination_location = destination_location
        self.alternate_identifier = None
        self.container_type = None
        self.est_delivery_date_local = None
        self.est_delivery_time_local = None
        self.guaranteed_delivery_date = None
        self.initial_delivery_attempt = "2025-10-16T17:07:08Z"
        self.object = "CarrierDetail"
        self.origin_tracking_location = MockEasypostTrackingLocation(
            city="NORTH HOUSTON", state="TX", zip_code="77315"
        )
        self.destination_tracking_location = MockEasypostTrackingLocation(
            city="CHARLESTON", state="SC", zip_code="29407"
        )


class MockEasypostFee:
    """Mock object for EasyPost Fee."""

    def __init__(self, fee_type="PostageFee", amount="4.46000", charged=True):
        self.type = fee_type
        self.amount = amount
        self.charged = charged
        self.refunded = False
        self.object = "Fee"


class MockEasypostVerificationDetails:
    """Mock object for address verification details."""

    def __init__(self, latitude=37.93592, longitude=-122.07187):
        self.latitude = latitude
        self.longitude = longitude
        self.time_zone = "America/Los_Angeles"


class MockEasypostVerification:
    """Mock object for address verification."""

    def __init__(self, success=True):
        self.details = MockEasypostVerificationDetails() if success else None
        self.errors = []
        self.success = success


class MockEasypostAddress:
    """Mock object for EasyPost Address with verifications."""

    def __init__(
        self,
        address_id="adr_test123",
        name="Test Company",
        street1="123 Main St",
        city="San Francisco",
        state="CA",
        zip_code="94134",
        country="US",
        phone="4155550100",
        email=None,
        company=None,
        residential=None,
        verify=False,
    ):
        self.id = address_id
        self.name = name
        self.company = company or name
        self.street1 = street1
        self.street2 = None
        self.city = city
        self.state = state
        self.zip = zip_code
        self.country = country
        self.phone = phone
        self.email = email
        self.residential = residential
        self.carrier_facility = None
        self.federal_tax_id = None
        self.state_tax_id = None
        self.object = "Address"
        self.mode = "test"
        self.created_at = "2025-11-14T03:13:06Z"
        self.updated_at = "2025-11-14T03:13:08Z"

        # Verifications
        if verify:
            self.verifications = {
                "delivery": MockEasypostVerification(success=True),
                "zip4": MockEasypostVerification(success=True),
            }
        else:
            self.verifications = {}


class MockEasypostParcel:
    """Mock object for EasyPost Parcel."""

    def __init__(
        self,
        parcel_id="prcl_test123",
        weight=0.5,
        length=None,
        width=None,
        height=None,
    ):
        self.id = parcel_id
        self.weight = weight
        self.length = length
        self.width = width
        self.height = height
        self.predefined_package = None
        self.object = "Parcel"
        self.mode = "test"
        self.created_at = "2025-11-14T03:13:06Z"
        self.updated_at = "2025-11-14T03:13:06Z"


class MockEasypostRate:
    """Mock object for EasyPost Rate response."""

    def __init__(
        self,
        rate="10.50",
        currency="USD",
        carrier="USPS",
        service="Priority",
        carrier_account_id="ca_d8fb2ed778024a3c9065309cfcf76d6f",
        rate_id=None,
        shipment_id="shp_test123",
        delivery_days=2,
        delivery_date_guaranteed=False,
    ):
        self.id = rate_id or "rate_test123"
        self.rate = rate
        self.currency = currency
        self.carrier = carrier
        self.service = service
        self.carrier_account_id = carrier_account_id
        self.shipment_id = shipment_id

        # Additional real fields
        self.list_rate = str(float(rate) * 1.1)  # Typically higher
        self.list_currency = currency
        self.retail_rate = str(float(rate) * 1.3)  # Retail pricing
        self.retail_currency = currency
        self.delivery_days = delivery_days
        self.est_delivery_days = delivery_days
        self.delivery_date = None
        self.delivery_date_guaranteed = delivery_date_guaranteed
        self.billing_type = "easypost"

        # Metadata
        self.object = "Rate"
        self.mode = "test"
        self.created_at = "2025-11-14T03:13:07Z"
        self.updated_at = "2025-11-14T03:13:07Z"

    def get(self, key, default=None):
        """Provide dictionary-like access to attributes."""
        return getattr(self, key, default)


class MockEasypostPostageLabel:
    """Mock object for EasyPost PostageLabel."""

    def __init__(
        self,
        label_id="pl_test123",
        label_url=None,
        label_format="PDF",
        label_size="8.5x11",
    ):
        self.id = label_id
        self.object = "PostageLabel"

        # Label URLs
        default_url = "https://easypost-files.s3.us-west-2.amazonaws.com/"
        default_postage_label = (
            "postage_label/20251114/e81a8bc7027c5e4689bbd52baa83cdf0c4.pdf"
        )
        self.label_url = label_url or f"{default_url}/files/{default_postage_label}"
        self.label_pdf_url = self.label_url if label_format == "PDF" else None
        self.label_epl2_url = None
        self.label_zpl_url = None
        self.label_file = None

        # Label properties
        self.label_file_type = "application/pdf"
        self.label_type = "default"
        self.label_size = label_size
        self.label_resolution = 300
        self.label_date = "2025-11-14T03:13:06Z"
        self.date_advance = 0
        self.integrated_form = "none"

        # Timestamps
        self.created_at = "2025-11-14T03:13:08Z"
        self.updated_at = "2025-11-14T03:13:08Z"


class MockEasypostTracker:
    """Mock object for EasyPost Tracker with full tracking history."""

    def __init__(
        self,
        tracker_id="trk_test123",
        tracking_code="9400100208303110928988",
        carrier="USPS",
        status="delivered",
        public_url=None,
        shipment_id="shp_test123",
        signed_by="John Tester",
    ):
        self.id = tracker_id
        self.tracking_code = tracking_code
        self.carrier = carrier
        self.status = status
        self.status_detail = "arrived_at_destination"
        self.shipment_id = shipment_id
        self.signed_by = signed_by

        # URLs
        self.public_url = (
            public_url
            or "https://track.easypost.com/djE6dHJrX2NkMmZkYzEyYzc3NDQ0NjNiMzJkNTg5MWM3NzA0ODdi"
        )

        # Carrier details
        self.carrier_detail = MockEasypostCarrierDetail()

        # Tracking history
        self.tracking_details = [
            MockEasypostTrackingDetail(
                datetime_str="2025-10-14T03:16:08Z",
                message="Pre-Shipment Info Sent to USPS",
                status="pre_transit",
                status_detail="status_update",
                tracking_location=MockEasypostTrackingLocation(),
            ),
            MockEasypostTrackingDetail(
                datetime_str="2025-10-14T15:53:08Z",
                message="Shipping Label Created",
                status="pre_transit",
                status_detail="status_update",
                tracking_location=MockEasypostTrackingLocation(
                    city="HOUSTON", state="TX", zip_code="77063"
                ),
            ),
            MockEasypostTrackingDetail(
                datetime_str="2025-10-15T01:58:08Z",
                message="Arrived at USPS Origin Facility",
                status="in_transit",
                status_detail="arrived_at_facility",
                tracking_location=MockEasypostTrackingLocation(
                    city="NORTH HOUSTON", state="TX", zip_code="77315"
                ),
            ),
            MockEasypostTrackingDetail(
                datetime_str="2025-10-16T06:25:08Z",
                message="Arrived at Post Office",
                status="in_transit",
                status_detail="arrived_at_facility",
                tracking_location=MockEasypostTrackingLocation(
                    city="CHARLESTON", state="SC", zip_code="29407"
                ),
            ),
            MockEasypostTrackingDetail(
                datetime_str="2025-10-16T12:15:08Z",
                message="Out for Delivery",
                status="out_for_delivery",
                status_detail="out_for_delivery",
                tracking_location=MockEasypostTrackingLocation(
                    city="CHARLESTON", state="SC", zip_code="29407"
                ),
            ),
            MockEasypostTrackingDetail(
                datetime_str="2025-10-16T17:07:08Z",
                message="Delivered",
                status="delivered",
                status_detail="arrived_at_destination",
                tracking_location=MockEasypostTrackingLocation(
                    city="CHARLESTON", state="SC", zip_code="29407"
                ),
            ),
        ]

        # Additional fields
        self.est_delivery_date = "2025-11-14T03:16:08Z"
        self.weight = None
        self.delivery_evidence = []
        self.fees = []

        # Metadata
        self.object = "Tracker"
        self.mode = "test"
        self.created_at = "2025-11-14T03:13:08Z"
        self.updated_at = "2025-11-14T03:16:09Z"

    def get(self, key, default=None):
        """Provide dictionary-like access to attributes."""
        return getattr(self, key, default)


class MockEasypostShipment:
    """Mock object for EasyPost Shipment response with complete structure."""

    def __init__(
        self,
        shipment_id="shp_c8769fdd3b32423da240b36cac5813ce",
        tracking_code="9400100208303110928988",
        rate="4.46",
        currency="USD",
        carrier="USPS",
        service="GroundAdvantage",
        carrier_account_id="ca_d8fb2ed778024a3c9065309cfcf76d6f",
        label_url=None,
        public_url=None,
        reference="WH/OUT/00017",
        insurance="50.00",
    ):
        # Basic identification
        self.id = shipment_id
        self.object = "Shipment"
        self.mode = "test"
        self.reference = reference
        self.tracking_code = tracking_code

        # Timestamps
        self.created_at = "2025-11-14T03:13:06Z"
        self.updated_at = "2025-11-14T03:18:08Z"

        # Addresses (as full Address objects)
        self.from_address = MockEasypostAddress(
            address_id="adr_from_test",
            name=MOCK_ADDRESS_FROM["name"],
            street1=MOCK_ADDRESS_FROM["street1"],
            city=MOCK_ADDRESS_FROM["city"],
            state=MOCK_ADDRESS_FROM["state"],
            zip_code=MOCK_ADDRESS_FROM["zip"],
            country=MOCK_ADDRESS_FROM["country"],
            phone=MOCK_ADDRESS_FROM["phone"],
            email=MOCK_ADDRESS_FROM["email"],
        )

        self.to_address = MockEasypostAddress(
            address_id="adr_to_test",
            name=MOCK_ADDRESS_TO["name"],
            street1=MOCK_ADDRESS_TO["street1"],
            city=MOCK_ADDRESS_TO["city"],
            state=MOCK_ADDRESS_TO["state"],
            zip_code=MOCK_ADDRESS_TO["zip"],
            country=MOCK_ADDRESS_TO["country"],
            phone=MOCK_ADDRESS_TO["phone"],
            email=MOCK_ADDRESS_TO["email"],
            verify=True,
        )

        self.return_address = self.from_address
        self.buyer_address = self.to_address

        # Parcel
        self.parcel = MockEasypostParcel(
            weight=MOCK_PARCEL_DATA["weight"],
            length=MOCK_PARCEL_DATA["length"],
            width=MOCK_PARCEL_DATA["width"],
            height=MOCK_PARCEL_DATA["height"],
        )

        # Options
        self.options = MOCK_OPTIONS.copy()
        self.options["label_date"] = "2025-11-14T03:13:06+00:00"

        # Insurance
        self.insurance = insurance

        # Rates - create multiple rates from different carriers
        self.rates = [
            MockEasypostRate(
                rate="4.46",
                carrier="USPS",
                service="GroundAdvantage",
                carrier_account_id="ca_d8fb2ed778024a3c9065309cfcf76d6f",
                rate_id="rate_5021fae54237478a898bb6b6d7ae57f2",
                shipment_id=shipment_id,
                delivery_days=2,
            ),
            MockEasypostRate(
                rate="7.17",
                carrier="USPS",
                service="Priority",
                carrier_account_id="ca_d8fb2ed778024a3c9065309cfcf76d6f",
                rate_id="rate_700d64662a2e4a7a8bd0ad5c04b9e928",
                shipment_id=shipment_id,
                delivery_days=2,
            ),
            MockEasypostRate(
                rate="6.04",
                carrier="UPSDAP",
                service="Ground",
                carrier_account_id="ca_9e600251a342490ab1858692594407e8",
                rate_id="rate_76a2882c29014ad889bbda08fa469581",
                shipment_id=shipment_id,
                delivery_days=1,
            ),
        ]

        # Selected rate
        self.selected_rate = MockEasypostRate(
            rate=rate,
            currency=currency,
            carrier=carrier,
            service=service,
            carrier_account_id=carrier_account_id,
            shipment_id=shipment_id,
        )

        # Postage label
        self.postage_label = MockEasypostPostageLabel(label_url=label_url)

        # Tracker
        self.tracker = MockEasypostTracker(
            tracking_code=tracking_code,
            carrier=carrier,
            public_url=public_url,
            shipment_id=shipment_id,
        )

        # Fees
        self.fees = [
            MockEasypostFee("LabelFee", "0.00000", True),
            MockEasypostFee("PostageFee", rate, True),
            MockEasypostFee("InsuranceFee", "0.65000", True),
        ]

        # Messages (errors/warnings from carriers)
        DHL_MESSAGE = "DHL Express default accounts are prohibited"
        self.messages = [
            {
                "carrier": "DHLExpress",
                "carrier_account_id": "ca_fa595e9631ed4532b28784b8c069e72e",
                "message": f"{DHL_MESSAGE} for existing DHL Express users.",
                "type": "rate_error",
            }
        ]

        # Additional fields
        self.status = "delivered"
        self.is_return = False
        self.usps_zone = 1
        self.batch_id = None
        self.batch_status = None
        self.batch_message = None
        self.customs_info = None
        self.forms = []
        self.scan_form = None
        self.refund_status = None
        self.order_id = None

    def lowest_rate(self, carriers=None, services=None):
        """
        Mock lowest_rate method.

        Returns the rate with the lowest price from available rates.
        """
        if carriers or services:
            # Filter rates based on criteria
            filtered_rates = self.rates
            if carriers:
                carrier_list = carriers if isinstance(carriers, list) else [carriers]
                filtered_rates = [
                    r for r in filtered_rates if r.carrier in carrier_list
                ]
            if services:
                service_list = services if isinstance(services, list) else [services]
                filtered_rates = [
                    r for r in filtered_rates if r.service in service_list
                ]

            if filtered_rates:
                return min(filtered_rates, key=lambda r: float(r.rate))

        # Return lowest rate overall
        return min(self.rates, key=lambda r: float(r.rate))

    def buy(self, rate=None, end_shipper_id=None):
        """
        Mock buy method.

        Updates selected_rate if rate is provided, simulating shipment purchase.
        """
        if rate:
            self.selected_rate = rate
        self.status = "delivered"
        return self


class MockEasypostEndShipper:
    """Mock object for EasyPost EndShipper."""

    def __init__(self, shipper_id="es_test123", **address_data):
        self.id = shipper_id
        # Store address data
        for key, value in address_data.items():
            setattr(self, key, value)


class MockEasypostBatch:
    """Mock object for EasyPost Batch."""

    def __init__(
        self,
        batch_id="batch_test123",
        state="created",
        num_shipments=0,
        shipments=None,
    ):
        self.id = batch_id
        self.state = state
        self.num_shipments = num_shipments
        self.shipments = shipments or []


class MockEasypostError:
    """Mock object for EasyPost Error."""

    def __init__(self, message="API Error", errors=None):
        self.message = message
        self.errors = errors or [
            {
                "message": message,
                "http_body": "Error details from API",
            }
        ]


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================


def create_mock_shipment(
    shipment_id="shp_test",
    tracking_code="TRACK123",
    rate="10.50",
    carrier="USPS",
    service="Priority",
):
    """
    Helper to create a MockEasypostShipment with common defaults.

    Args:
        shipment_id: Shipment ID
        tracking_code: Tracking code
        rate: Rate amount as string
        carrier: Carrier name
        service: Service name

    Returns:
        MockEasypostShipment instance
    """
    return MockEasypostShipment(
        shipment_id=shipment_id,
        tracking_code=tracking_code,
        rate=rate,
        carrier=carrier,
        service=service,
    )


def create_mock_rate(rate="10.50", carrier="USPS", service="Priority"):
    """
    Helper to create a MockEasypostRate.

    Args:
        rate: Rate amount as string
        carrier: Carrier name
        service: Service name

    Returns:
        MockEasypostRate instance
    """
    return MockEasypostRate(rate=rate, carrier=carrier, service=service)


def create_mock_end_shipper(shipper_id="es_test", **address_kwargs):
    """
    Helper to create a MockEasypostEndShipper.

    Args:
        shipper_id: EndShipper ID
        **address_kwargs: Address data to include

    Returns:
        MockEasypostEndShipper instance
    """
    address_data = MOCK_ADDRESS_FROM.copy()
    address_data.update(address_kwargs)
    return MockEasypostEndShipper(shipper_id=shipper_id, **address_data)


def create_mock_end_shippers_response(count=1):
    """
    Helper to create EndShipper.all() response.

    Args:
        count: Number of end shippers to include

    Returns:
        Dict with 'end_shippers' key containing list of mock end shippers
    """
    return {"end_shippers": [{"id": f"es_test{i}"} for i in range(count)]}


def create_mock_error(message="API Error", http_body="Error details"):
    """
    Helper to create a MockEasypostError.

    Args:
        message: Error message
        http_body: HTTP body details

    Returns:
        MockEasypostError instance
    """
    return MockEasypostError(
        message=message,
        errors=[{"message": message, "http_body": http_body}],
    )


def mock_requests_get_label(content=b"PDF_BINARY_CONTENT"):
    """
    Helper to create a mock for requests.get() when fetching labels.

    Args:
        content: Binary content to return

    Returns:
        Mock response object
    """
    mock_response = Mock()
    mock_response.content = content
    mock_response.status_code = 200
    return mock_response


# =============================================================================
# MULTIPLE SHIPMENTS HELPERS
# =============================================================================


def create_multiple_mock_shipments(count=2, base_id="shp_test", base_tracking="TRACK"):
    """
    Helper to create multiple mock shipments.

    Args:
        count: Number of shipments to create
        base_id: Base shipment ID (will be suffixed with index)
        base_tracking: Base tracking code (will be suffixed with index)

    Returns:
        List of MockEasypostShipment instances
    """
    return [
        create_mock_shipment(
            shipment_id=f"{base_id}{i}",
            tracking_code=f"{base_tracking}{i}",
            rate=str(10.0 + i),
        )
        for i in range(count)
    ]


def create_mock_batch_shipments_data(count=2):
    """
    Helper to create batch shipment data structure.

    Args:
        count: Number of shipments

    Returns:
        List of dicts with shipment batch data
    """
    shipments = create_multiple_mock_shipments(count)
    return [
        {
            "id": ship.id,
            "carrier": ship.selected_rate.carrier,
            "service": ship.selected_rate.service,
        }
        for ship in shipments
    ]
