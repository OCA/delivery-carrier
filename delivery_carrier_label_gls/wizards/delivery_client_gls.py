# -*- coding: utf-8 -*-
# Copyright 2021 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
# pylint: disable=unbalanced-tuple-unpacking

import logging

import requests

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

HEADERS = {  # a GLS service constant.
    "Accept": "application/glsVersion1+json, application/json",
    "Content-Type": "application/glsVersion1+json",
}


class DeliveryClientGls(models.TransientModel):
    _name = "delivery.client.gls"
    _description = "GLS API client"

    carrier_id = fields.Many2one("delivery.carrier", "Carrier", required=True)

    @api.constrains("carrier_id")
    def _constrain_carrier(self):
        for record in self:
            if record.carrier_id.delivery_type != "gls":
                raise ValidationError(_("This is a GLS client."))

    def _get_contact_id(self):
        self.ensure_one()
        contact_id = self.carrier_id.company_id.gls_contact_id
        if not contact_id:
            raise ValidationError(_("Your GLS Contact ID is not configured."))
        return contact_id

    def _get_gls_connections_parameters(self):
        self.ensure_one()
        test_mode = self.carrier_id.company_id.gls_test
        keys = ["gls_url_test" if test_mode else "gls_url"]
        keys += ["gls_login", "gls_password"]
        parameters = []
        for key in keys:
            value = self.carrier_id[key]
            if not value:
                msg = _("The %s is missing in the delivery configuration.")
                raise ValidationError(msg % key)
            parameters.append(value)
        return parameters

    def get_end_of_day_report(self, date=False):
        date = date or fields.Date.today()
        if isinstance(date, str):  # v10
            date = fields.Date.from_string(date)
        params = {"date": fields.Date.to_string(date)}
        return self._post("shipments/endofday", params=params)

    def validate_parcel(self, payload):
        payload["Shipment"]["Product"] = "PARCEL"
        payload["Shipment"]["Shipper"] = {"ContactID": self._get_contact_id()}
        return self._post("shipments/validate", json=payload)

    def create_parcel(self, payload):
        payload["Shipment"]["Shipper"] = {"ContactID": self._get_contact_id()}
        payload["PrintingOptions"] = {
            "ReturnLabels": {
                "TemplateSet": self.carrier_id.gls_label_template or "NONE",
                "LabelFormat": self.carrier_id.gls_label_format.upper(),
            }
        }
        return self._post("shipments", json=payload)

    def cancel_parcel(self, parcel_tracking):
        end_url = "shipments/cancel/%s" % parcel_tracking
        response = self._post(end_url)
        if response["result"] not in ["CANCELLED", "CANCELLATION_PENDING"]:
            raise ValidationError(_("This package cannot be cancelled anymore."))
        return response

    def getAllowedServices(self, payload):
        return self._post("shipments/allowedservices", json=payload)

    def getParcelShopsByCountryCode(self, country_code):
        return self._get("parcelshop/country/%s" % country_code)

    def _get(self, url_endpoint, **kwargs):
        return self._request(requests.get, url_endpoint, **kwargs)

    def _post(self, url_endpoint, **kwargs):
        return self._request(requests.post, url_endpoint, **kwargs)

    def _request(self, verb, url_endpoint, **kwargs):
        root_url, login, password = self._get_gls_connections_parameters()
        url = root_url + url_endpoint if url_endpoint else root_url
        response = verb(url, auth=(login, password), headers=HEADERS, **kwargs)
        _logger.info(response)
        if not response.ok:
            error = _("GLS: cannot perform this operation. Original error: %s")
            msg = response.headers.get("message") or response.text
            message = " ".join((str(response.status_code), msg or _("Unknown error.")))
            raise ValidationError(error % message)
        return response.json()
