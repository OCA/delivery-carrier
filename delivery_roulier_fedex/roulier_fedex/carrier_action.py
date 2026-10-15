#  Copyright (c) 2026 Groupe Voltaire
#  @author Emilie SOUTIRAS  <emilie.soutiras@groupevoltaire.com>
#  License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from roulier.carrier_action import CarrierGetLabel, CarrierWebservice
from roulier.roulier import factory

from .api import FedexApiCancel, FedexApiParcel
from .constants import (
    CANCEL_ENDPOINT,
    CARRIER_TYPE,
    PRODUCTION_URL,
    SANDBOX_URL,
    SHIP_ENDPOINT,
)
from .decoder import FedexDecoderCancel, FedexDecoderGetLabel
from .encoder import FedexCancelEncoder, FedexEncoder
from .transport import FedexTransport


class FedexGetLabel(CarrierGetLabel):
    base_url = PRODUCTION_URL
    base_test_url = SANDBOX_URL
    endpoint = SHIP_ENDPOINT
    http_method = "post"
    ws_url = PRODUCTION_URL + SHIP_ENDPOINT
    ws_test_url = SANDBOX_URL + SHIP_ENDPOINT
    encoder = FedexEncoder
    decoder = FedexDecoderGetLabel
    transport = FedexTransport
    api = FedexApiParcel
    manage_multi_label = True


class FedexCancelShipment(CarrierWebservice):
    base_url = PRODUCTION_URL
    base_test_url = SANDBOX_URL
    endpoint = CANCEL_ENDPOINT
    http_method = "put"
    ws_url = PRODUCTION_URL + CANCEL_ENDPOINT
    ws_test_url = SANDBOX_URL + CANCEL_ENDPOINT
    encoder = FedexCancelEncoder
    decoder = FedexDecoderCancel
    transport = FedexTransport
    api = FedexApiCancel

    def cancel_shipment(self, carrier_type, action, data):
        return self._get_data_from_webservice(data)


factory.register_builder(CARRIER_TYPE, "get_label", FedexGetLabel)
factory.register_builder(CARRIER_TYPE, "cancel_shipment", FedexCancelShipment)
