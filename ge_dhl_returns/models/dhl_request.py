import binascii
import json

from odoo import _

from odoo.addons.ge_dhl_base.models.dhl_request import DhlRequest as DhlRequestBase


class DhlRequest(DhlRequestBase):
    def __init__(self, carrier, record, api="dhl_return"):
        super(DhlRequest, self).__init__(carrier, record, api=api)

    def _prepare_return_label_request(self, picking_id):
        data = {
            "receiverId": self.receiverId,
            "customerReference": picking_id.origin,
            "shipmentReference": picking_id.name,
            "shipper": {
                "name1": picking_id.partner_id.name,
                "name2": "",
                "name3": "",
                "addressStreet": picking_id.partner_id.street,
                "addressHouse": picking_id.partner_id.street_number,
                "city": picking_id.partner_id.city,
                "email": picking_id.partner_id.email,
                "phone": picking_id.partner_id.phone,
                "postalCode": picking_id.partner_id.zip,
                # "state": "NRW"
            },
            "itemWeight": {"uom": "kg", "value": picking_id.shipping_weight},
            "itemValue": {"currency": "EUR", "value": 100},
        }
        return json.dumps(data)

    def dhl_parcel_de_provider_get_return_label(
        self, picking_id, tracking_number, origin_date
    ):
        # if package.delivery_state != "customer_delivered":
        domain = "https://api-sandbox.dhl.com"
        endpoint = "/parcel/de/shipping/returns/v1/orders"
        params = "labelType=BOTH"
        url = f"{domain}{endpoint}?{params}"
        response = self._send_api_request(
            url="%s" % url,
            data=self._prepare_return_label_request(picking_id),
            auth=True,
            method="POST",
            content_type="application/json",
        )
        data = json.loads(response)

        label_data = data.get("label", {}).get("b64")
        qr_label_data = data.get("qrLabel", {}).get("b64")
        binary_data = binascii.a2b_base64(str(label_data))
        qr_binary_data = binascii.a2b_base64(str(qr_label_data))
        tracking_number = data.get("shipmentNo")
        message = _("Label created!<br/> <b>Shipping  Number : </b>%s<br/>") % (
            tracking_number,
        )
        picking_id.message_post(
            body=message,
            attachments=[("Label-%s.%s" % (tracking_number, "pdf"), binary_data)],
        )

        picking_id.message_post(
            body=message,
            attachments=[("QRLabel-%s.%s" % (tracking_number, "png"), qr_binary_data)],
        )
