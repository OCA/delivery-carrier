# Copyright 2021-2022 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import base64
import logging

import requests

from odoo import _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class DhlRequest(object):
    def __init__(self, carrier, record, api=None):
        if api is None:
            _logger.warning(
                "DhlRequest needs to be initialized with api='' "
                "dhl_tracking, dhl_shipping, dhl_return"
            )
        self.carrier = carrier
        self.record = record
        self.username = getattr(self.carrier.company_id, api + "_userid", False)
        self.password = getattr(self.carrier.company_id, api + "_password", False)
        self.dhl_api_key = getattr(self.carrier.company_id, api + "_dhl_api_key", False)
        self.dhl_api_secret = getattr(
            self.carrier.company_id, api + "_dhl_api_secret", False
        )
        self.domain = getattr(self.carrier.company_id, api + "_domain", False)
        self.endpoint = getattr(self.carrier.company_id, api + "_endpoint", False)
        self.url = getattr(self.carrier.company_id, api + "_url", False)
        self.receiverId = getattr(self.carrier.company_id, api + "_receiverId", False)

        if api in ["dhl_return", "dhl_shipping"]:
            user = self.username
            password = self.password
        else:
            user = self.dhl_api_key
            password = self.dhl_api_secret
        auth_encoding = "%s:%s" % (
            user,
            password,
        )
        self.authorization = base64.b64encode(auth_encoding.encode("utf-8")).decode(
            "utf-8"
        )

    def _send_api_request(
        self, url, data=None, auth=True, content_type="application/xml", method="GET"
    ):
        if data is None:
            data = {}
        dhl_last_request = ("URL: {}\nData: {}").format(self.url, data)
        self.carrier.log_xml(dhl_last_request, "dhl_last_request")
        try:
            headers = {"Content-Type": content_type, "charset": "UTF-8"}
            if auth:
                headers["Authorization"] = "Basic {}".format(self.authorization)
                headers["dhl-api-key"] = "{}".format(self.dhl_api_key)
            res = requests.request(
                method, url=url, data=data.encode("utf-8"), headers=headers, timeout=60
            )
            res.raise_for_status()
            self.carrier.log_xml(res.text or "", "dhl_last_request")
            res = res.text
        except requests.exceptions.Timeout as tout:
            raise UserError(_("Timeout: the server did not reply within 60s")) from tout
        except (ValueError, requests.exceptions.ConnectionError) as valerr:
            raise UserError(
                _("Server not reachable, please try again later")
            ) from valerr
        except requests.exceptions.HTTPError as e:
            _logger.warning(e)
            resp = res.json()

            errormessage = ""
            for line in resp.get("items", []):
                for valmes in line.get("validationMessages", []):
                    errormessage += valmes.get("validationMessage", "")

            raise UserError(
                _(
                    "%(error)s\n%(message)s\n%(detail)s%(errormessage)s\n%(fullresponse)s"
                )
                % {
                    "error": e,
                    "message": resp.get("Message", "") if res.text else "",
                    "detail": resp.get("detail", "") if res.text else "",
                    "errormessage": errormessage,
                    "fullresponse": res.text,
                }
            ) from e
        return res
