#  Copyright (c) 2026 Groupe Voltaire
#  @author Emilie SOUTIRAS  <emilie.soutiras@groupevoltaire.com>
#  License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from roulier.codec import DecoderBase, DecoderGetLabel
from roulier.exception import CarrierError

_logger = logging.getLogger(__name__)

TRACKING_URL = "https://www.fedex.com/fedextrack/?trknbr=%s"


def _label_type(doc_type):
    return "ZPL" if doc_type == "ZPLII" else doc_type


def _log_alerts(alerts):
    for alert in alerts or []:
        _logger.warning(
            "FedEx %s %s: %s",
            alert.get("alertType", "NOTE"),
            alert.get("code"),
            alert.get("message"),
        )


class FedexDecoderGetLabel(DecoderGetLabel):
    def decode(self, response, input_payload):
        output = response["body"].get("output", {})
        _log_alerts(output.get("alerts"))
        requested_shipment = input_payload["body"]["requestedShipment"]
        label_format = requested_shipment["labelSpecification"]["imageType"]
        input_parcels = (self.config.roulier_input or {}).get("parcels", [])
        for shipment in output.get("transactionShipments", []):
            _log_alerts(shipment.get("alerts"))
            for index, piece in enumerate(shipment.get("pieceResponses", [])):
                self.result["parcels"].append(
                    self._decode_piece(piece, index, input_parcels, label_format)
                )
            self.result["annexes"] += self._decode_shipment_documents(shipment)

    def _decode_piece(self, piece, index, input_parcels, label_format):
        tracking_number = piece["trackingNumber"]
        reference = tracking_number
        if index < len(input_parcels):
            reference = input_parcels[index].get("reference") or tracking_number
        documents = [
            doc for doc in piece.get("packageDocuments", []) if doc.get("encodedLabel")
        ]
        if not documents:
            raise CarrierError(
                None,
                [
                    {
                        "id": tracking_number,
                        "message": "FedEx returned no label for package %s"
                        % tracking_number,
                    }
                ],
            )
        document = documents[0]
        return {
            "id": tracking_number,
            "reference": reference,
            "tracking": {
                "number": tracking_number,
                "url": TRACKING_URL % tracking_number,
                "partner": "",
            },
            "label": {
                "data": document["encodedLabel"],
                "name": tracking_number,
                "type": _label_type(document.get("docType") or label_format),
            },
        }

    def _decode_shipment_documents(self, shipment):
        return [
            {
                "name": (document.get("contentType") or "document").lower(),
                "type": _label_type(document.get("docType") or "PDF").lower(),
                "data": document["encodedLabel"],
            }
            for document in shipment.get("shipmentDocuments", [])
            if document.get("encodedLabel")
        ]


class FedexDecoderCancel(DecoderBase):
    def __init__(self, config_object):
        super().__init__(config_object)
        self.result = {}

    def decode(self, response, payload):
        output = response["body"].get("output", {})
        _log_alerts(output.get("alerts"))
        self.result = {
            "cancelled": bool(output.get("cancelledShipment")),
            "message": output.get("successMessage", ""),
        }
