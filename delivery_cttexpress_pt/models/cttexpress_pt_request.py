# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import logging
import uuid

from lxml import etree
from zeep import Client
from zeep.helpers import serialize_object
from zeep.plugins import HistoryPlugin

_logger = logging.getLogger(__name__)

CTTEXPRESS_PT_API_URL = {
    # TODO: The QA environment doesn't seem reachable. Check with CTT.
    "test": "http://logistica.cttexpresso.pt:8082/CTTExpressoWSQ/"
    "CTTShipmentProviderWS.svc?singleWsdl",
    "prod": "http://cttexpressows.ctt.pt/cttewspool/"
    "CTTShipmentProviderWS.svc?singleWsdl",
}


def log_request(method):
    """Decorator to write raw request/response in the CTT request object"""

    def wrapper(*args, **kwargs):
        res = method(*args, **kwargs)
        try:
            args[0].ctt_last_request = etree.tostring(
                args[0].history.last_sent["envelope"],
                encoding="UTF-8",
                pretty_print=True,
            )
            args[0].ctt_last_response = etree.tostring(
                args[0].history.last_received["envelope"],
                encoding="UTF-8",
                pretty_print=True,
            )
        # Don't fail hard on this. Sometimes zeep can't keep history
        except Exception:
            return res
        return res

    return wrapper


class CTTExpressPTRequest:
    """Interface between the CTT Express Portugal e-pool SOAP API.

    Wraps the ShipmentProvider WS operations: CreateShipment,
    CreateShipmentWithoutPrint, CompleteShipment and CloseShipment.
    """

    def __init__(
        self,
        authentication_id,
        client_id,
        contract_id,
        distribution_channel_id,
        user_id,
        prod=False,
    ):
        self.authentication_id = authentication_id
        self.client_id = client_id
        self.contract_id = contract_id
        self.distribution_channel_id = distribution_channel_id
        self.user_id = user_id
        self.history = HistoryPlugin(maxlen=10)
        # We'll store raw xml request/responses in this properties
        self.ctt_last_request = False
        self.ctt_last_response = False
        self.client = Client(
            wsdl=CTTEXPRESS_PT_API_URL["prod" if prod else "test"],
            plugins=[self.history],
        )

    def _input(self, extra=None):
        """Common input fields for every operation."""
        values = {
            "AuthenticationID": self.authentication_id,
            "RequestID": str(uuid.uuid4()),
            "UserID": self.user_id,
        }
        if extra:
            values.update(extra)
        return values

    @log_request
    def create_shipment(self, delivery_note):
        """Create a shipment, returning documents and object codes.

        :param dict delivery_note: DeliveryNote values prepared from Odoo
        :return dict: Serialized CreateShipment response
        """
        response = self.client.service.CreateShipment(
            Input=self._input({"DeliveryNote": delivery_note})
        )
        return serialize_object(response)

    @log_request
    def create_shipment_without_print(self, delivery_note):
        """Create a shipment without generating the shipping label.

        :param dict delivery_note: DeliveryNote values prepared from Odoo
        :return dict: Serialized CreateShipmentWithoutPrint response
        """
        response = self.client.service.CreateShipmentWithoutPrint(
            Input=self._input({"DeliveryNote": delivery_note})
        )
        return serialize_object(response)

    @log_request
    def complete_shipment(self, delivery_note):
        """Complete a previously created shipment.

        :param dict delivery_note: DeliveryNote values prepared from Odoo
        :return dict: Serialized CompleteShipment response
        """
        response = self.client.service.CompleteShipment(
            Input=self._input({"DeliveryNote": delivery_note})
        )
        return serialize_object(response)

    @log_request
    def close_shipment(self, shipments):
        """Close shipments to obtain the carrier manifest documents.

        :param list shipments: Shipment2Close dicts with FirstObjectCode,
            LastObjectCode and SubProductCode
        :return dict: Serialized CloseShipment response
        """
        response = self.client.service.CloseShipment(
            Input=self._input(
                {
                    "ClientId": self.client_id,
                    "ContractId": self.contract_id,
                    "DistributionChannel": self.distribution_channel_id,
                    "ListOfShipmentToClose": {"Shipment2Close": shipments},
                }
            )
        )
        return serialize_object(response)

    def test_connection(self):
        """Probe the API with a CloseShipment for nonexistent object codes.

        The service has no ping operation; closing shipments that do not
        exist cannot have side effects and the ErrorsList reply proves
        connectivity and authentication.

        :return dict: Serialized CloseShipment response
        """
        return self.close_shipment(
            [
                {
                    "FirstObjectCode": "CONNECTIONTEST0PT",
                    "LastObjectCode": "CONNECTIONTEST0PT",
                    "SubProductCode": "TEST",
                }
            ]
        )
