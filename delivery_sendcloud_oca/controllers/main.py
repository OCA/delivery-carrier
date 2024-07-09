# Copyright 2024 Onestein (<https://www.onestein.nl>)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl)

import base64
import hmac
import io
import json
import logging

import PyPDF2

from odoo import fields, http
from odoo.http import content_disposition, request

_logger = logging.getLogger(__name__)


class DeliverySendcloud(http.Controller):
    @http.route(["/sendcloud/picking/download_labels"], type="http", auth="user")
    def sendcloud_picking_download_labels(self, ids, **post):
        picking_ids = []
        for picking_id in ids.split(","):
            picking_ids.append(int(picking_id))
        pickings = request.env["stock.picking"].browse(picking_ids)
        file_data = []
        for attachment in pickings.mapped("sendcloud_parcel_ids").mapped(
            "attachment_id"
        ):
            file_data.append(base64.b64decode(attachment.datas))

        if not file_data:
            return

        pdf_merger = PyPDF2.PdfFileMerger()
        for pdf_data in file_data:
            pdf_file = io.BytesIO(pdf_data)
            pdf_merger.append(pdf_file, import_bookmarks=False)

        new_stream = io.BytesIO()
        pdf_merger.write(new_stream)
        new_stream.seek(0)
        pdf = new_stream.read()

        file_name = "labels.pdf"  # Change the file name as needed
        headers = [
            ("Content-Type", "application/pdf"),
            ("Content-Length", len(pdf)),
            ("Content-Disposition", content_disposition(file_name)),
        ]
        return request.make_response(pdf, headers)

    @http.route(
        "/shop/sendcloud_integration_webhook/<int:company_id>",
        methods=["POST"],
        type="json",
        auth="none",
    )
    def sendcloud_integration_webhook(self, company_id, **kwargs):
        payload_data = request.get_json_data()
        _logger.info("Sendcloud payload_data:%s", str(payload_data))
        integration = self._verify_sendcloud_authentic(payload_data, company_id)
        if integration:
            _logger.info("Sendcloud integration.id:%s", integration.id)
            timestamp = payload_data.get("timestamp")
            sendcloud_action = (
                request.env["sendcloud.action"]
                .sudo()
                .create(
                    {
                        "company_id": company_id,
                        "sendcloud_integration_id": integration.id,
                        "message_type": "received",
                        "action": payload_data.get("action"),
                        "message": json.dumps(payload_data),
                        "timestamp": str(timestamp) if timestamp else False,
                    }
                )
            )
            sendcloud_action.sudo().reparse_message()

    def _verify_sendcloud_authentic(self, payload, company_id):
        received_signature = request.httprequest.headers.get("sendcloud-signature")
        _logger.info("Sendcloud received_signature:%s", received_signature)
        if received_signature:
            encoded_payload = json.dumps(payload).encode("utf-8")
            action = payload.get("action")
            _logger.info("Sendcloud action:%s", action)
            company = request.env["res.company"].sudo().browse(company_id)
            integrations = company.sendcloud_integration_ids
            if action != "integration_credentials":
                integrations = integrations.filtered(
                    lambda i: i.public_key and i.secret_key
                )
                for integration in integrations:
                    secret_key = integration.secret_key.encode("utf-8")
                    signature = hmac.new(
                        key=secret_key, msg=encoded_payload, digestmod="sha256"
                    )
                    if signature.hexdigest() == received_signature:
                        return integration
            else:
                secret_key = payload.get("secret_key").encode("utf-8")
                signature = hmac.new(
                    key=secret_key, msg=encoded_payload, digestmod="sha256"
                )
                if signature.hexdigest() == received_signature:
                    _logger.info("Sendcloud signature:%s", signature)
                    integrations = integrations.filtered(
                        lambda i: not i.public_key
                        and not i.secret_key
                        and not i.sendcloud_code
                    )
                    integration = fields.first(integrations)
                    _logger.info("Sendcloud integration:%s", integration.id)
                    return integration
        return request.env["sendcloud.integration"]
