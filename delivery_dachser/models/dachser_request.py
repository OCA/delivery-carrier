# Copyright 2025 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import json

import requests

from odoo import _, fields
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_round

from .dachser_master_data import DACHSER_SHIPMENT_STATUS


class DachserRequest:
    def __init__(self, carrier):
        self.carrier_id = carrier
        self.division = self.carrier_id.dachser_division
        product_f_name = f"dachser_product_{self.division.lower()}"
        self.product = self.carrier_id[product_f_name]
        self.term = self.carrier_id.dachser_term
        packaging_f_name = f"dachser_packaging_{self.division.lower()}"
        self.packaging = self.carrier_id[packaging_f_name]
        self.default_packaging = self.carrier_id.dachser_default_packaging_id
        # There are no different URLs for test/prod
        path = "https://api-gateway.dachser.com"
        self.urls = {
            "rate_shipment": f"{path}/rest/v2/quotations",
            "shipment": f"{path}/rest/v2/transportorders/sent",
            "tracking": f"{path}/rest/v2/shipmentstatus",
            "cancel": f"{path}/rest/v2/transportorders",
        }

    def _send_api_request(self, request_type, url, data=None):
        data = data if data else {}
        result = {}
        headers = {"X-API-Key": self.carrier_id.dachser_api_key}
        try:
            if request_type == "GET":
                res = requests.get(url=url, headers=headers, params=data, timeout=60)
            elif request_type == "POST":
                res = requests.post(url=url, headers=headers, json=data, timeout=60)
            elif request_type == "DELETE":
                res = requests.delete(url=url, headers=headers, json=data, timeout=60)
            else:
                raise UserError(
                    _(
                        "Unsupported request type, please only use 'GET', 'POST' "
                        "or 'DELETE'"
                    )
                )
            try:
                result = res.json()
            except json.JSONDecodeError:
                result = res.text
            dachser_last_request = f"URL: {url}\nData: {data}"
            self.carrier_id.log_xml(dachser_last_request, "dachser_last_request")
            self.carrier_id.log_xml(result, "dachser_last_response")
        except requests.exceptions.Timeout as tmo:
            raise UserError(_("Timeout: the server did not reply within 60s")) from tmo
        except Exception as e:
            raise UserError(
                _("{error}\n{result}".format(error=e, result=result if result else ""))
            ) from e
        return res

    def _prepare_quotation_data(self, order):
        partner_shipping = order.partner_shipping_id
        return {
            "transportOrder": {
                "transportDate": order.expected_date.strftime("%Y-%m-%d"),
                "division": self.division,
                "product": self.product,
                "term": self.term,
                "consignee": {
                    "addressInformation": {
                        "postalCode": partner_shipping.zip,
                        "countryCode": partner_shipping.country_id.code,
                    }
                },
                "transportOrderLines": [
                    {
                        "quantity": line.product_uom_qty,
                        "packaging": self.packaging,
                        "weight": {
                            "weight": int(
                                float_round(
                                    (line.product_id.weight * line.product_uom_qty),
                                    precision_digits=0,
                                    rounding_method="UP",
                                )
                            ),
                            "unit": line.product_id.weight_uom_name.upper(),
                        },
                    }
                    for line in order.order_line.filtered(lambda x: not x.display_type)
                ],
            }
        }

    def rate_shipment(self, order):
        response = self._send_api_request(
            request_type="POST",
            url=self.urls["rate_shipment"],
            data=self._prepare_quotation_data(order),
        )
        res = {"price": 0, "error_message": False}
        if response.status_code == 200:
            res["price"] = response.json()["totalAmount"]["amount"]
        else:
            res["error_message"] = response.json().get("message", False)
        return res

    def _prepare_shipment_data(self, picking):
        partner = picking.partner_id
        streets = [partner.street]
        if partner.street2:
            streets.append(partner.street2)
        return {
            "transportDate": fields.Datetime.now().strftime("%Y-%m-%d"),
            "division": self.division,
            "product": self.product,
            "term": self.term,
            "consignee": {
                "names": [partner.name],
                "addressInformation": {
                    "streets": streets,
                    "city": partner.city,
                    "postalCode": partner.zip,
                    "countryCode": partner.country_id.code,
                },
            },
            "references": [{"code": "100", "value": picking.name}],
            "transportOrderLines": [
                {
                    "quantity": picking.number_of_packages or 1,
                    "packaging": self.packaging,
                    # It is required to define an explanatory text, therefore, we use
                    # the description_picking field.
                    "content": picking.move_ids_without_package[:1].description_picking,
                    "weight": {
                        "weight": int(
                            float_round(
                                picking.shipping_weight,
                                precision_digits=0,
                                rounding_method="UP",
                            )
                        )
                        if picking.shipping_weight
                        else 1,
                        "unit": "KG",
                    },
                    "measure": {
                        "length": self.default_packaging.packaging_length,
                        "width": self.default_packaging.width,
                        "height": self.default_packaging.height,
                        "unit": "CM",
                        "volume": {"amount": picking.volume, "unit": "M3"},
                    },
                }
            ],
        }

    def send_shipping(self, picking):
        response = self._send_api_request(
            request_type="POST",
            url=self.urls["shipment"],
            data=self._prepare_shipment_data(picking),
        )
        res = {"tracking_number": False, "label": False}
        if response.status_code == 201:
            response_json = response.json()
            res["tracking_number"] = response_json["id"]
            res["label"] = response_json["label"]
        else:
            raise UserError(response.json()["message"])
        return res

    def cancel_shipping(self, picking):
        cancel_url = self.urls["cancel"]
        response = self._send_api_request(
            request_type="DELETE",
            url=f"{cancel_url}/{picking}",
        )
        return True if response.status_code == 200 else False

    def get_tracking(self, shipping_code):
        response = self._send_api_request(
            request_type="GET",
            url=self.urls["tracking"],
            data={"tracking-number": shipping_code},
        )
        res = {
            "delivery_state": False,
            "tracking_state": False,
            "tracking_events": [],
        }
        if response.status_code == 200:
            shipment = response.json()["shipments"][-1]
            for status in shipment["status"]:
                event_code = status["event"]["code"]
                event_description = status["event"]["description"]
                res["tracking_events"].append(
                    {
                        "statusDate": status["statusDate"],
                        "code": event_code,
                        "description": event_description,
                    }
                )
                if status["statusSequence"] == 1:
                    res["tracking_state"] = event_description
                    res["delivery_state"] = DACHSER_SHIPMENT_STATUS.get(
                        event_code, "shipping_recorded_in_carrier"
                    )
            # Need to reverse the list so that it is in proper order (oldest first).
            res["tracking_events"] = res["tracking_events"][::-1]
        return res
