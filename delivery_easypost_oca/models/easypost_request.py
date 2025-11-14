import logging

import easypost
import requests

from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


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
        response = requests.get(self.label_url)
        return response.content


class EasypostRequest:
    def __init__(self, carrier):
        self.carrier = carrier
        self.debug_logger = self.carrier.log_xml
        self.api_key = self.carrier.easypost_oca_test_api_key
        if self.carrier.prod_environment:
            self.api_key = self.carrier.easypost_oca_production_api_key

        easypost.api_key = self.api_key
        self.client = easypost

    def create_end_shipper(self, address):
        try:
            if not address["street2"]:
                address["street2"] = address["street1"]

            end_shipper = self.client.end_shipper.create(**address)
        except Exception as e:
            raise UserError(self._get_message_errors(e)) from e
        return end_shipper

    def create_multiples_shipments(self, shipments: list, batch_mode=False) -> list:
        if batch_mode:
            return self.create_shipments_batch(shipments)
        return self.create_shipments(shipments)

    def create_shipments_batch(self, shipments: list):
        created_shipments = self.create_shipments(shipments)
        return [
            {
                "id": shipment.id,
                "carrier": shipment.lowest_rate().carrier,
                "service": shipment.lowest_rate().service,
            }
            for shipment in created_shipments
        ]

    def create_shipments(self, shipments: list):
        created_shipments = []
        for shipment in shipments:
            _ship = self.create_shipment(
                to_address=shipment["to_address"],
                from_address=shipment["from_address"],
                parcel=shipment["parcel"],
                options=shipment["options"],
                reference=shipment["reference"],
                carrier_accounts=shipment["carrier_accounts"],
            )
            created_shipments.append(_ship)
        return created_shipments

    def create_shipment(
        self,
        from_address: dict,
        to_address: dict,
        parcel: dict,
        options=None,
        reference=None,
        carrier_accounts=None,
    ):
        if options is None:
            options = {}
        if carrier_accounts is None:
            carrier_accounts = []
        try:
            created_shipment = self.client.Shipment.create(
                from_address=from_address,
                to_address=to_address,
                parcel=parcel,
                options=options,
                reference=reference,
                carrier_accounts=carrier_accounts,
            )
        except Exception as e:
            raise UserError(self._get_message_errors(e)) from e
        return created_shipment

    def buy_shipments(self, shipments, carrier_services=None):
        bought_shipments = []
        for shipment in shipments:
            bought_shipments.append(self.buy_shipment(shipment, carrier_services))
        return bought_shipments

    @staticmethod
    def _get_selected_rate(shipment, carrier_services=None):
        return shipment.lowest_rate()

    def buy_shipment(self, shipment, carrier_services=None):
        selected_rate = self._get_selected_rate(shipment, carrier_services)
        end_shipper = None
        if selected_rate.carrier in ("USPS", "UPS"):
            end_shippers = self.client.EndShipper.all(page_size=1)["end_shippers"]
            if not end_shippers:
                end_shipper = self.create_end_shipper(shipment.from_address)["id"]
            else:
                end_shipper = end_shippers[0]["id"]
        try:
            bought_shipment = shipment.buy(
                rate=selected_rate, end_shipper_id=end_shipper
            )
        except easypost.Error as error:
            raise UserError(self._get_message_errors(error)) from error

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

    def retreive_shipment(self, shipment_id: str):
        try:
            shipment = self.client.shipment.Retrieve(id=shipment_id)
        except Exception as e:
            raise UserError(self._get_message_errors(e)) from e
        return shipment

    def retreive_multiple_shipment(self, ids: list):
        return [self.retreive_shipment(id) for id in ids]

    def calculate_shipping_rate(
        self, from_address: dict, to_address: dict, parcel: dict, options: dict
    ):
        _shipment = self.create_shipment(
            from_address=from_address,
            to_address=to_address,
            parcel=parcel,
            options=options,
        )
        return _shipment.lowest_rate()

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

    def label_batch(self, batch_id: str, file_format: str):
        try:
            label = self.client.batch.Label(id=batch_id, file_format=file_format)
        except Exception as e:
            raise UserError(self._get_message_errors(e)) from e
        return label

    def retreive_batch(self, batch_id: str):
        try:
            batch = self.client.batch.retrieve(id=batch_id)
        except Exception as e:
            raise UserError(self._get_message_errors(e)) from e
        return batch

    def track_shipment(self, tracking_number: str):
        tracker = self.client.tracker.create(tracking_code=tracking_number)
        return tracker

    def retrieve_shipment(self, shipment_id: str):
        return self.client.shipment.retrieve(id=shipment_id)

    def retrieve_carrier_metadata(self):
        return self.client.beta.CarrierMetadata.retrieve_carrier_metadata()

    def retrieve_all_carrier_accounts(self):
        try:
            carrier_accounts = self.client.CarrierAccount.all()
        except Exception as e:
            raise UserError(self._get_message_errors(e)) from e
        return carrier_accounts

    def _get_message_errors(self, e: easypost.Error) -> str:
        if not hasattr(e, "errors"):
            return getattr(e, "message", str(e))
        return "\n".join(
            [
                f"Error: {err['message']}\nError Body: {err['http_body']}"
                for err in e.errors
            ]
        )
