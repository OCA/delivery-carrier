import logging
from concurrent import futures

import requests

from odoo import _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

try:
    import easypost
except ImportError as err:
    _logger.error("Failed to import EasyPost: %s", err)


class EasyPostShipment:
    def __init__(
        self,
        shipment_id,
        tracking_code,
        label_url,
        public_url,
        rate,
        currency,
        carrier_id,
        carrier_name,
        carrier_service,
    ):
        self.shipment_id = shipment_id
        self.tracking_code = tracking_code
        self.label_url = label_url
        self.public_url = public_url
        self.rate = rate
        self.currency = currency
        self.carrier_id = carrier_id
        self.carrier_name = carrier_name
        self.carrier_service = carrier_service

    def get_label_content(self):
        try:
            response = requests.get(self.label_url, timeout=30)
            response.raise_for_status()  # Raise exception for HTTP errors
        except requests.RequestException as e:
            _logger.error(_("Failed to retrieve label content: %s"), e)
            raise UserError(_("Failed to retrieve label content.")) from e
        return response.content


class EasypostRequest:
    def __init__(self, carrier):
        self.carrier = carrier
        self.api_key = self._get_api_key()
        easypost.api_key = self.api_key
        self.client = easypost

    def _get_api_key(self):
        """Retrieve the API key based on the environment."""
        if self.carrier.prod_environment:
            return self.carrier.easypost_oca_production_api_key
        return self.carrier.easypost_oca_test_api_key

    def create_end_shipper(self, address):
        """Create an end shipper using the provided address."""
        try:
            address.setdefault("street2", address["street1"])
            return self.client.EndShipper.create(**address)
        except Exception as e:
            _logger.error("Failed to create end shipper: %s", e)
            raise UserError(self._get_message_errors(e)) from e

    def _get_message_errors(self, e: Exception) -> str:
        """Retrieve error messages from exceptions."""
        error_message = str(e)
        error_body = getattr(e, "http_body", "No HTTP body available")
        return f"Error: {error_message}\nError Body: {error_body}"

    def calculate_shipping_rate(
        self,
        from_address: dict,
        to_address: dict,
        parcel: dict,
        options: dict = None,
    ):
        """
        Calculate the shipping rate for a given shipment configuration.

        :param from_address: Sender's address details.
        :param to_address: Recipient's address details.
        :param parcel: Details of the parcel being shipped.
        :param options: Optional additional shipping options.
        :return: The lowest available shipping rate.
        """
        options = options or {}
        try:
            shipment = self.client.Shipment.create(
                from_address=from_address,
                to_address=to_address,
                parcel=parcel,
                options=options,
            )
            return shipment.lowest_rate()
        except Exception as e:
            _logger.error("Failed to calculate shipping rate: %s", e)
            raise UserError(self._get_message_errors(e)) from e

    def create_multiples_shipments(self, shipments: list, **kwargs) -> list:
        created_shipments = []
        with futures.ThreadPoolExecutor(max_workers=5) as executor:
            __futures = [
                executor.submit(
                    self.create_shipment,
                    shipment,
                    **kwargs,
                )
                for shipment in shipments
            ]
            for future in futures.as_completed(__futures):
                try:
                    __shipment = future.result()
                    created_shipments.append(__shipment)
                except Exception as e:
                    _logger.error("Failed to create shipment: %s", e)
        return created_shipments

    def create_shipment(
        self,
        shipment: dict,
        **kwargs,
    ):
        """
        Create a shipment using the EasyPost API.
        :param from_address: Sender's address.
        :param to_address: Recipient's address.
        :param parcel: Parcel details.
        :param options: Additional options for the shipment.
        :param reference: Reference for the shipment.
        :param carrier_accounts: Carrier accounts list.
        :return: Created shipment object.
        """
        try:
            return self.client.Shipment.create(**shipment)
        except Exception as e:
            _logger.error("Failed to create shipment: %s", e)
            raise UserError(self._get_message_errors(e)) from e

    def buy_shipments(self, shipments, carrier_services=None):
        """Buy multiple shipments."""
        return [self.buy_shipment(shipment, carrier_services) for shipment in shipments]

    def buy_shipment(self, shipment, carrier_services=None):
        """Buy a shipment given the selected rate."""
        selected_rate = self._get_selected_rate(shipment, carrier_services)
        end_shipper_id = self._get_end_shipper_id(selected_rate, shipment)

        try:
            bought_shipment = shipment.buy(
                rate=selected_rate, end_shipper_id=end_shipper_id
            )
        except Exception as e:
            _logger.error("Failed to buy shipment: %s", e)
            raise UserError(self._get_message_errors(e)) from e

        return EasyPostShipment(
            shipment_id=bought_shipment.id,
            tracking_code=bought_shipment.tracking_code,
            label_url=bought_shipment.postage_label.label_url,
            public_url=bought_shipment.tracker.public_url,
            rate=float(bought_shipment.selected_rate.rate),
            currency=bought_shipment.selected_rate.currency,
            carrier_id=bought_shipment.selected_rate.carrier_account_id,
            carrier_name=bought_shipment.selected_rate.carrier,
            carrier_service=bought_shipment.selected_rate.service,
        )

    def create_batch(self, shipments: list):
        try:
            created_batch = self.client.batch.create(
                shipments=shipments,
            )
        except Exception as e:
            raise UserError(self._get_message_errors(e)) from e
        return created_batch

    def buy_batch(self, batch_id: str):
        try:
            bought_batch = self.client.batch.Buy(id=batch_id)
        except Exception as e:
            raise UserError(self._get_message_errors(e)) from e
        return bought_batch

    def _get_end_shipper_id(self, selected_rate, shipment):
        """Determine the end shipper ID for the shipment."""
        if selected_rate.get("carrier") in ("USPS", "UPS"):
            end_shippers = self.client.EndShipper.all(page_size=1).get(
                "end_shippers", []
            )
            end_shipper = (
                end_shippers[0]
                if end_shippers
                else self.create_end_shipper(shipment.from_address)
            )
            return end_shipper.get("id")
        return None

    @staticmethod
    def _get_selected_rate(shipment, carrier_services=None):
        """Retrieve the selected shipping rate."""
        return shipment.lowest_rate()

    def retrieve_shipment(self, shipment_id: str):
        """Retrieve a shipment by its ID."""
        try:
            return self.client.Shipment.retrieve(id=shipment_id)
        except Exception as e:
            _logger.error("Failed to retrieve shipment: %s", e)
            raise UserError(self._get_message_errors(e)) from e

    def retrieve_carrier_metadata(self):
        """Retrieve metadata for all carrier accounts."""
        try:
            return self.client.beta.CarrierMetadata.retrieve_carrier_metadata()
        except Exception as e:
            _logger.error("Failed to retrieve carrier metadata: %s", e)
            raise UserError(self._get_message_errors(e)) from e

    def retrieve_all_carrier_accounts(self):
        """Retrieve all carrier accounts."""
        try:
            return self.client.CarrierAccount.all()
        except Exception as e:
            _logger.error("Failed to retrieve carrier accounts: %s", e)
            raise UserError(self._get_message_errors(e)) from e
