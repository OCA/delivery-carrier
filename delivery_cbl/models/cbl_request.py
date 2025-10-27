# Copyright 2025 Manuel Regidor <manuel.regidor@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64
import logging
from datetime import datetime

import requests

from odoo import _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class CBLRequest:
    def __init__(self, carrier):
        self.user = carrier.cbl_user
        self.password = carrier.cbl_password
        self.client_code = carrier.cbl_client_code
        self.client_token = carrier.cbl_client_token

    def _send_request(self, op, url, headers, json=False):
        return getattr(requests, op)(
            url,
            json=json,
            headers=headers,
        )

    def _manage_errors(self, response, picking):
        if response.status_code != 200:
            raise UserError(
                _(
                    "CBL Shipping for picking %(picking)s could not be created. "
                    "Reason: %(reason)s",
                    picking=picking.name,
                    reason=response.reason,
                )
            )

    def _generate_auth(self):
        auth = "{}:{}".format(self.user or "", self.password or "")
        auth64 = base64.encodebytes(auth.encode("ascii"))[:-1]
        return {"Authorization": "Basic " + auth64.decode("utf-8")}

    def _generate_daily_token(self, picking):
        headers = {
            "Content-Type": "application/json",
        }
        headers = {**headers, **self._generate_auth()}
        json = {"clientToken": self.client_token}
        response = self._send_request(
            "get",
            "https://clientesws.cbl-logistica.com/api/v1.0/TokenAuth/Get",
            headers,
            json,
        )
        self._manage_errors(response, picking)
        return response.json().get("dailyToken")

    def _get_packages(self, picking):
        number_of_packages = picking.number_of_packages or 1
        packages = []
        for i in range(number_of_packages):
            packages.append(
                {
                    "packageNumber": i + 1,
                }
            )
        return packages

    def _generate_shipping_json(self, picking, daily_token):
        company = picking.company_id
        customer = picking.partner_id
        packages = self._get_packages(picking)
        vals = {
            "dailyToken": daily_token,
            "carrierReference": picking.name,
            # It is necessary to include a timestamp so a new shipping can be
            # properly created if it's been previously canceled.
            "clientReference": f"{picking.name}-{datetime.now()}",
            "clientCode": self.client_code,
            "sender": {
                "name": company.name,
                "street": company.street,
                "postalCode": company.zip,
                "city": company.city,
                "province": company.state_id.name,
                "country": company.country_id.name,
                "phone": company.phone,
                "NIF": company.vat,
                "email": company.email,
            },
            "receiver": {
                "name": customer.name,
                "street": f"{customer.street or ''} {customer.street2 or ''}",
                "postalCode": customer.zip,
                "city": customer.city,
                "province": customer.state_id.name,
                "country": customer.country_id.name,
                "phone": customer.phone,
                "NIF": customer.vat,
                "email": customer.email,
            },
            "numPackages": len(packages),
            "weight": picking.shipping_weight,
            "packages": packages,
            "freight": picking.carrier_id.cbl_freight_type,
        }
        if picking.carrier_id.cbl_cash_on_delivery and picking.sale_id:
            vals.update({"cashOnDelivery": picking.sale_id.amount_total})
        return vals

    def _send_shipping(self, picking):
        daily_token = self._generate_daily_token(picking)
        shipping_json = self._generate_shipping_json(picking, daily_token)
        headers = {
            "Content-Type": "application/json",
        }
        headers = {**headers, **self._generate_auth()}
        _logger.info(
            f"""
            Sending CBL shipping for picking {picking.name}
             with values {shipping_json}.
            """,
        )
        response = self._send_request(
            "post",
            "https://clientesws.cbl-logistica.com/api/v1.0/ShipmentRegistry/CreateShipment",
            headers,
            shipping_json,
        )
        self._manage_errors(response, picking)
        response = response.json()
        tracking_ref = response.get("carrierReference")
        _logger.info(
            f"""CBL shipping for picking {picking.name}
             created with tracking ref. {tracking_ref}.
            """,
        )
        return tracking_ref, response.get("packagesTags")

    def cancel_shipment(self, picking):
        deleted = False
        delete_type = (
            "DeletePendingShipments"
            if not picking.cbl_confirmed
            else "DeleteConfirmedShipments"
        )
        url = f"https://clientesws.cbl-logistica.com/api/v1.0/ShipmentRegistry/{delete_type}"
        daily_token = self._generate_daily_token(picking)
        tracking_ref = picking.carrier_tracking_ref
        headers = {
            "Content-Type": "application/json",
        }
        headers = {**headers, **self._generate_auth()}
        cancel_json = {
            "dailyToken": daily_token,
            "clientCode": self.client_code,
            "shipmentReferences": [tracking_ref],
        }
        _logger.info(
            f"""Cancelling CBL shipping for picking
             {picking.name} with tracking ref. {tracking_ref}.
            """
        )
        response = self._send_request("delete", url, headers, cancel_json)
        self._manage_errors(response, picking)
        response = response.json()
        if response.get("deletedShipments") == 1:
            deleted = True
            _logger.info(f"CBL shipping for picking {picking.name} cancelled.")
        else:
            _logger.error(
                f"CBL shipping for picking {picking.name} could not be cancelled."
            )
        return deleted

    def confirm_shipments(self, picking):
        confirmed = False
        daily_token = self._generate_daily_token(picking)
        headers = {
            "Content-Type": "application/json",
        }
        headers = {**headers, **self._generate_auth()}
        confirm_json = {
            "dailyToken": daily_token,
            "shipmentReferences": [picking.carrier_tracking_ref],
        }
        response = self._send_request(
            "post",
            "https://clientesws.cbl-logistica.com/api/v1.0/ShipmentRegistry/ConfirmDayShipments",
            headers,
            confirm_json,
        )
        self._manage_errors(response, picking)
        if response.json().get("generatedShipments") == 1:
            confirmed = True
            _logger.info(
                f"""CBL shipping for picking {picking.name} and
                 tracking number {picking.carrier_tracking_ref} confirmed.
                """
            )
        else:
            _logger.error(
                f"""
                CBL shipping for picking {picking.name} and tracking number
                 {picking.carrier_tracking_ref} could not be confirmed.
                """
            )
        return confirmed
