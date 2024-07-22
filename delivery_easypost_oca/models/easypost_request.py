from dataclasses import dataclass
from typing import List

import requests
from easypost import EasyPostClient
from easypost.errors.general.easypost_error import EasyPostError
from easypost.models.address import Address
from easypost.models.end_shipper import EndShipper
from easypost.models.rate import Rate
from easypost.models.shipment import Shipment

from odoo.exceptions import UserError

ENDSHIPPER_MESSAGE = "ProviderEndShipper address.name or address.company required"


class EasyPostAddress(Address):
    def _get_address_values(self):
        values = {}
        addr_fields = [
            "street1",
            "street2",
            "city",
            "zip",
            "phone",
            "email",
            "company",
            "name",
        ]
        for _field in addr_fields:
            if getattr(self.id, _field):
                values[_field] = getattr(self.id, _field)
        return values


@dataclass
class EasyPostShipment:
    id: str
    tracking_code: str
    label_url: str
    public_url: str
    rate: float
    currency: str
    carrier_id: str
    carrier_name: str

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
        self.client = EasyPostClient(self.api_key)

    def create_end_shipper(self, address: Address) -> EndShipper:
        try:
            new_address: EasyPostAddress = EasyPostAddress(address)
            end_shipper = self.client.end_shipper.create(
                **new_address._get_address_values()
            )
        except EasyPostError as e:
            raise UserError(self._get_message_errors(e))
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

    def create_shipments(self, shipments: list) -> List[Shipment]:
        created_shipments = []
        for shipment in shipments:
            _ship = self.create_shipment(
                to_address=shipment["to_address"],
                from_address=shipment["from_address"],
                parcel=shipment["parcel"],
                options=shipment["options"],
                reference=shipment["reference"],
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
    ) -> Shipment:
        if options is None:
            options = {}
        try:
            created_shipment = self.client.shipment.create(
                from_address=from_address,
                to_address=to_address,
                parcel=parcel,
                options=options,
                reference=reference,
            )
        except EasyPostError as e:
            raise UserError(self._get_message_errors(e))
        return created_shipment

    def buy_shipments(self, shipments: List[Shipment]) -> List[EasyPostShipment]:
        bought_shipments = []
        for shipment in shipments:
            bought_shipments.append(self.buy_shipment(shipment))
        return bought_shipments

    def buy_shipment(self, _shipment: Shipment) -> EasyPostShipment:
        try:
            rate: Rate = _shipment.lowest_rate()
            end_shipper = None
            if rate.carrier in ("USPS", "UPS"):
                end_shippers = self.client.end_shipper.all(page_size=1).end_shippers
                if not end_shippers:
                    end_shipper = self.create_end_shipper(_shipment.from_address).id
                else:
                    end_shipper = end_shippers[0].id

            bought_shipment = self.client.shipment.buy(
                id=_shipment.id,
                rate=rate,
                end_shipper_id=end_shipper,
            )
        except EasyPostError as e:
            error_message = self._get_message_errors(e)
            raise UserError(error_message)

        return EasyPostShipment(
            id=bought_shipment.id,
            tracking_code=bought_shipment.tracking_code,
            label_url=bought_shipment.postage_label.label_url,
            public_url=bought_shipment.tracker.public_url,
            rate=float(bought_shipment.selected_rate.rate),
            currency=bought_shipment.selected_rate.currency,
            carrier_id=bought_shipment.selected_rate.carrier_account_id,
            carrier_name=bought_shipment.selected_rate.carrier,
        )

    def retreive_shipment(self, shipment_id: str):
        try:
            shipment = self.client.shipment.retrieve(id=shipment_id)
        except EasyPostError as e:
            raise UserError(self._get_message_errors(e))
        return shipment

    def retreive_multiple_shipment(self, ids: list):
        return [self.retreive_shipment(id) for id in ids]

    def calculate_shipping_rate(
        self, from_address: dict, to_address: dict, parcel: dict, options: dict
    ):
        """
        Calculate the shipping rate for a given parcel, origin, and destination.

        Args:
            parcel (Parcel): The parcel to be shipped.
            origin (Address): The origin address.
            destination (Address): The destination address.

        Returns:
            float: The lowest shipping rate for the given parcel, origin, and destination.
        """
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
        except EasyPostError as e:
            raise UserError(self._get_message_errors(e))
        return created_batch

    def buy_batch(self, batch_id: str):
        try:
            bought_batch = self.client.batch.buy(id=batch_id)
        except EasyPostError as e:
            raise UserError(self._get_message_errors(e))
        return bought_batch

    def label_batch(self, batch_id: str, file_format: str):
        try:
            label = self.client.batch.label(id=batch_id, file_format=file_format)
        except EasyPostError as e:
            raise UserError(self._get_message_errors(e))
        return label

    def retreive_batch(self, batch_id: str):
        try:
            batch = self.client.batch.retrieve(id=batch_id)
        except EasyPostError as e:
            raise UserError(self._get_message_errors(e))
        return batch

    def track_shipment(self, tracking_number: str):
        tracker = self.client.tracker.create(tracking_code=tracking_number)
        return tracker

    def retrieve_shipment(self, shipment_id: str):
        return self.client.shipment.retrieve(id=shipment_id)

    def _get_message_errors(self, e: EasyPostError) -> str:
        if not e.errors:
            return e.message
        return "\n".join([err["message"] for err in e.errors])
