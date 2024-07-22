import json
import logging

from odoo import http
from odoo.http import request

from ..models.easypost_request import EasypostRequest

_logger = logging.getLogger(__name__)


class EasyPostWebhook(http.Controller):
    @http.route(
        ["/easypost_webhook"],
        type="json",
        auth="public",
    )
    def webhook_batch(self):
        _logger.info(f"Webhook Request ==> {request.jsonrequest}")
        easypost_carrier = (
            request.env["delivery.carrier"]
            .sudo()
            .search([("delivery_type", "=", "easypost_oca")], limit=1)
        )
        ep_request = EasypostRequest(easypost_carrier)
        json_body = request.jsonrequest.get("result", {})
        _object = json_body.get("object", False)
        state = json_body.get("state")
        if _object == "Batch":
            batch_id = json_body.get("id")
            picking = self._get_picking_by_batch_id(batch_id)
            if not picking:
                return json.dumps(
                    {
                        "status": "error",
                        "message": "Picking not found",
                    }
                )

            if state == "created":
                picking.message_post(body="Batch created")
                _logger.info("created")
            elif state == "purchased":
                picking.message_post(body="Batch postage_purchased")
                _logger.info("postage_purchased")
            elif state == "label_generated":
                picking.message_post(body="Batch label_generated")
                _logger.info("label_generated")

        elif _object == "Tracker":
            shipment_id = json_body.get("shipment_id")
            state = json_body.get("status")
            picking = self._get_picking_by_shipment_id(ep_request, shipment_id)

            if state in ("delivered", "pre_transit", "pending"):
                tracking_code = json_body.get("tracking_code")
                carrier = json_body.get("carrier")
                public_url = json_body.get("public_url")
                carrier_tracking_link = (
                    f"<a target='_blank' href='{public_url}'> {tracking_code}</a>"
                )

                logmessage = f"Shipment created into Easypost<br/> <b>Tracking Numbers:</b> {carrier_tracking_link}<br/> <b>Carrier Account:</b> {carrier}<br/>"
                picking.message_post(body=logmessage)

            _logger.info("Tracker")

    def _get_picking_by_batch_id(self, batch_id):
        return (
            request.env["stock.picking"]
            .sudo()
            .search([("easypost_oca_batch_id", "=", batch_id)], limit=1)
        )

    def _get_picking_by_shipment_id(self, ep: EasypostRequest, shipment_id):
        shipment = ep.retreive_shipment(shipment_id)
        return (
            request.env["stock.picking"]
            .sudo()
            .search([("easypost_oca_batch_id", "=", shipment.batch_id)], limit=1)
        )
