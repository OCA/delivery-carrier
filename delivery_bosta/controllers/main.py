# Copyright 2026 Yahia Sherif
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import hmac
import json

from odoo import SUPERUSER_ID, fields, http
from odoo.http import request

from ..models.delivery_carrier import BOSTA_DELIVERY_STATES, BOSTA_STATES

MAX_BODY_BYTES = 64 * 1024


class BostaWebhook(http.Controller):
    @http.route(
        "/delivery_bosta/webhook",
        type="http",
        auth="public",
        methods=["POST"],
        csrf=False,
    )
    def bosta_webhook(self):
        received = request.httprequest.headers.get("Authorization", "").encode()
        carriers = (
            request.env["delivery.carrier"]
            .sudo()
            .with_context(active_test=False)
            .search(
                [("delivery_type", "=", "bosta"), ("bosta_webhook_secret", "!=", False)]
            )
            .filtered(
                lambda c: hmac.compare_digest(c.bosta_webhook_secret.encode(), received)
            )
        )
        if not carriers:
            return request.make_json_response({"error": "unauthorized"}, status=401)

        if (request.httprequest.content_length or 0) > MAX_BODY_BYTES:
            return request.make_json_response({"error": "body too large"}, status=413)
        raw = request.httprequest.get_data()
        if len(raw) > MAX_BODY_BYTES:
            return request.make_json_response({"error": "body too large"}, status=413)
        try:
            body = json.loads(raw)
        except ValueError:
            body = None
        if not isinstance(body, dict):
            return request.make_json_response(
                {"error": "expected a JSON object"}, status=400
            )

        tracking_number = str(body.get("trackingNumber") or "")
        pickings = tracking_number and (
            request.env["stock.picking"]
            .with_user(SUPERUSER_ID)
            .search(
                [
                    ("carrier_id", "in", carriers.ids),
                    ("carrier_tracking_ref", "ilike", tracking_number),
                ]
            )
            .filtered(lambda p: tracking_number in p.carrier_tracking_ref.split(","))
        )
        if not pickings:
            return request.make_json_response({"status": "ignored"})

        try:
            code = int(body.get("state"))
        except (TypeError, ValueError):
            code = None
        label = BOSTA_STATES.get(code) or f"State {str(body.get('state'))[:20]}"
        try:
            timestamp = float(body.get("timeStamp"))
        except (TypeError, ValueError):
            timestamp = 0.0
        updated = pickings.filtered(
            lambda p: timestamp > p.bosta_tracking_timestamp
            if timestamp
            else label != p.tracking_state
        )
        now = fields.Datetime.now()
        for picking in updated:
            vals = {
                "tracking_state": label,
                "tracking_state_history": "\n".join(
                    filter(None, [picking.tracking_state_history, f"{now} {label}"])
                ),
                "bosta_tracking_timestamp": timestamp
                or picking.bosta_tracking_timestamp,
            }
            if code in BOSTA_DELIVERY_STATES:
                vals["delivery_state"] = BOSTA_DELIVERY_STATES[code]
            if vals.get("delivery_state") == "customer_delivered":
                vals["date_delivered"] = now
            picking.write(vals)
        return request.make_json_response({"status": "ok" if updated else "unchanged"})
