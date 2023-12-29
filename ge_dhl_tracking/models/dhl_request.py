# Copyright 2021-2022 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import base64
import logging

import dicttoxml
import requests

from odoo import _
from odoo.exceptions import UserError
import xmltodict
from datetime import datetime
import binascii

_logger = logging.getLogger(__name__)
dicttoxml.LOG.setLevel(logging.ERROR)


def slicen(s, n, truncate=False):
    assert n > 0
    while len(s) >= n:
        yield s[:n]
        s = s[n:]
    if len(s) and not truncate:
        yield s


class DhlRequest(object):
    def __init__(self, carrier, record):
        self.carrier = carrier
        self.record = record

        self.username = self.carrier.company_id.dhl_tracking_userid
        self.password = self.carrier.company_id.dhl_tracking_password

        self.dhl_tracking_dhl_api_key = self.carrier.company_id.dhl_tracking_dhl_api_key
        self.dhl_tracking_dhl_api_secret = (
            self.carrier.company_id.dhl_tracking_dhl_api_secret
        )
        self.dhl_tracking_domain = self.carrier.company_id.dhl_tracking_domain
        self.dhl_tracking_endpoint = self.carrier.company_id.dhl_tracking_endpoint
        self.url = self.carrier.company_id.dhl_tracking_url
        auth_encoding = "%s:%s" % (
            self.dhl_tracking_dhl_api_key,
            self.dhl_tracking_dhl_api_secret,
        )
        self.authorization = base64.b64encode(auth_encoding.encode("utf-8")).decode(
            "utf-8"
        )

    def _send_api_request(
        self, url, data=None, auth=True, content_type="application/xml"
    ):
        if data is None:
            data = {}
        dhl_last_request = ("URL: {}\nData: {}").format(self.url, data)
        self.carrier.log_xml(dhl_last_request, "dhl_last_request")
        try:
            headers = {"Content-Type": content_type, "charset": "UTF-8"}
            if auth:
                headers["Authorization"] = "Basic {}".format(self.authorization)
                headers["dhl-api-key"] = "{}".format(self.dhl_tracking_dhl_api_key)
            res = requests.get(
                url=url, data=data.encode("utf-8"), headers=headers, timeout=60
            )
            res.raise_for_status()
            self.carrier.log_xml(res.text or "", "dhl_last_response")
            res = res.text
        except requests.exceptions.Timeout as tout:
            raise UserError(_("Timeout: the server did not reply within 60s")) from tout
        except (ValueError, requests.exceptions.ConnectionError) as valerr:
            raise UserError(
                _("Server not reachable, please try again later")
            ) from valerr
        except requests.exceptions.HTTPError as e:
            _logger.warning(e)
            raise UserError(
                _("{}\n{}").format(e, res.json().get("Message", "") if res.text else "")
            ) from e
        return res

    def _get_tracking_id(self, picking_id):
        tracking_infos = []
        for tracking_id in picking_id.get_tracking_ids():

            # it's not allowed to request already delivered packages
            # remove after testing / we reuse the test numbers.
            # if package.delivery_state != "customer_delivered":
            if True:
                xml = (
                    'xml=<?xml version="1.0" encoding="ISO-8859-1" standalone="no"?>'
                    f'<data appname="{self.username}" language-code="de" '
                    f'password="{self.password}" '
                    f'piece-code="{tracking_id}" request="d-get-signature"/>'
                )
                url = f"{self.url}?{xml}"
                response = self._send_api_request(
                    url="%s" % url,
                    auth=True,
                )
                content = xmltodict.parse(response)
                res = content.get("data", {}).get("data", {})
                image = res.get("@image")

                binary_data = b""
                filename = ""
                if image:
                    for a, b in slicen(image, 2):
                        binary_data += binascii.unhexlify(f"{a}{b}")

                    binary_data = base64.b64encode(binary_data)
                    mime_type = res.get("@mime-type", "")
                    ending = mime_type.split("/")[-1]
                    filename = f"signature.{ending}"

                # get tracking information
                params = (
                    'xml=<?xml version="1.0" encoding="UTF-8" '
                    f'standalone="no"?><data appname="{self.username}" '
                    f'language-code="en" password="{self.password}" '
                    f'piece-code="{tracking_id}" '
                    'request="d-get-piece-detail"/>'
                )
                url = f"{self.url}?{params}"
                response = self._send_api_request(
                    url="%s" % url,
                    data=self._prepare_tracking_request(),
                    auth=True,
                )
                content = xmltodict.parse(response)
                res = content.get("data", {}).get("data", {})
                res2 = res.get("data", {}).get("data", {})
                for line in res2:
                    tracking = {
                        "name": line.get("@event-status", False),
                        "event_timestamp": datetime.strptime(
                            line.get("@event-timestamp", False), "%d.%m.%Y %H:%M"
                        ),
                        "ice": line.get("@ice", False),
                        "ric": line.get("@ric", False),
                        "event_location": line.get("@event-location", False),
                        "event_country": line.get("@event-country", False),
                        "standard_event_code": line.get("@standard-event-code", False),
                        "ruecksendung": line.get("@ruecksendung", False),
                        "piece_code": tracking_id,
                    }
                    if image:
                        tracking["image"] = binary_data
                        tracking["filename"] = filename

                    tracking_infos.append(tracking)

                if "ERROR" in response:
                    errors = response["ERROR"]
                    if type(errors) is not list:
                        errors = [errors]
                    raise UserError(
                        _("Sending to DHL\n%s")
                        % (
                            "\n".join(
                                "%(CODE)s %(DESCRIPTION)s" % error for error in errors
                            )
                        )
                    )

        return tracking_infos

    def tracking_state_update(self):
        picking_id = self.record
        # updates the tracking.event, these compute the status at the package level
        tracking_ids = self._get_tracking_id(picking_id)
        picking_id.carrier_id.add_tracking_info_to_db(tracking_ids)

        # we than set the status on the picking level. If all packages are
        # delivered we set it to "customer_delivered" and use the latest date
        # if the two packages are delivered at different times.
        # in case one package is not yet delivered the state
        # multiple_states is used.
        delivery_state = False
        all_delivered = True
        latest_delivery = datetime(1990, 1, 1)
        for package in picking_id.package_ids:
            if package.delivery_state != "customer_delivered":
                all_delivered = False
            else:
                if package.date_delivered and package.date_delivered > latest_delivery:
                    latest_delivery = package.date_delivered

        if not all_delivered:
            delivery_state = "multiple_states"
        else:
            delivery_state = "customer_delivered"
        return {
            "delivery_state": delivery_state,
            "date_delivered": latest_delivery,
        }
