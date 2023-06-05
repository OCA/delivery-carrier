# Copyright 2022 FactorLibre - Jorge Martínez <jorge.martinez@factorlibre.com>
# Copyright 2022 FactorLibre - Zahra Velasco <zahra.velasco@factorlibre.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import requests

from odoo import _
from odoo.exceptions import UserError


class DelivereaRequest(object):
    def __init__(self, carrier):
        self.carrier_id = carrier
        path = (
            self.carrier_id.deliverea_url_prod
            if self.carrier_id.prod_environment
            else self.carrier_id.deliverea_url_test
        )
        if path[-1] != "/":
            path += "/"
        self.urls = {
            "distribution_centers": path + "distribution-centers",
            "carriers": path + "distribution-centers/{distributionCenterId}/carriers",
            "carrier_services": path + "distribution-centers/{distributionCenterId}"
            "/carriers/{carrierCode}/cost-centers/{costCenter}",
            "carrier_services_integrations": path
            + "carriers/{carrierCode}/integrations/{integration_code}",
            "create_shipment": path + "shipments",
            "delete_shipment": path + "shipments/{delivereaReference}",
            "get_shipment_label": path + "shipments/{delivereaReference}/label",
            "create_return": path + "returns",
            "get_shipment_tracking": path + "shipments/{delivereaReference}/trackings",
            "get_return_tracking": path + "returns/{delivereaReference}/trackings",
        }

    def _send_api_request(self, request_type, url, data=None, skip_auth=False):
        if data is None:
            data = {}
        try:
            auth = tuple()
            if not skip_auth:
                auth = tuple(
                    [
                        self.carrier_id.deliverea_username,
                        self.carrier_id.deliverea_password,
                    ]
                )
            if request_type == "GET":
                res = requests.get(url=url, auth=auth, timeout=60)
            elif request_type == "POST":
                res = requests.post(url=url, auth=auth, json=data, timeout=60)
            elif request_type == "PUT":
                res = requests.put(url=url, auth=auth, json=data, timeout=60)
            elif request_type == "DELETE":
                res = requests.delete(url=url, auth=auth, json=data, timeout=60)
            else:
                raise UserError(
                    _("Unsupported request type, use 'GET', 'POST', 'UPDATE', 'DELETE'")
                )
        except requests.exceptions.Timeout as exc_timeout:
            raise UserError(
                _("Timeout: the server did not reply within 60s")
            ) from exc_timeout
        if res.status_code == 202:
            return True
        if res.status_code not in range(200, 299):
            self._check_error(res.json())
        return res

    def _check_error(self, res):
        error = res.get("error", False) or res.get("errors", False)
        if error:
            if isinstance(error, list):
                error = error[0]
            return_code = error.get("code")
            message = error.get("message")
            detail = error.get("detail", "")
            if return_code:
                raise UserError(
                    _("%(name)s: %(rcode)s %(message)s %(detail)s %(ccode)s")
                    % {
                        "name": _("Deliverea Error"),
                        "rcode": return_code,
                        "message": message,
                        "detail": " ".join(
                            ["%s: %s" % (key, value) for key, value in detail.items()]
                        )
                        if detail and not isinstance(detail, str)
                        else detail or "",
                        "ccode": "\n{}: {} {}".format(
                            _("Carrier Error"),
                            error.get("carrierCode"),
                            error.get("carrierMessage"),
                        )
                        if error.get("carrierCode")
                        else "",
                    }
                )
        else:
            raise UserError(
                _(
                    "Deliverea Error. "
                    "Uncontrolled error, it is necessary to check the log"
                )
            )

    def get_distribution_centers(self):
        res = self._send_api_request(
            request_type="GET", url=self.urls["distribution_centers"]
        )
        return res.json()

    def get_carrier_list(self, distribution_center_id):
        res = self._send_api_request(
            request_type="GET",
            url=self.urls["carriers"].format(
                distributionCenterId=distribution_center_id
            ),
        )
        return res.json()

    def get_carrier_detail(self, distribution_center_id, carrier_code, cost_center):
        res = self._send_api_request(
            request_type="GET",
            url=self.urls["carrier_services"].format(
                carrierCode=carrier_code,
                distributionCenterId=distribution_center_id,
                costCenter=cost_center,
            ),
        )
        return res.json()

    def get_carrier_services_integrations(self, carrier_code, integration_code):
        res = self._send_api_request(
            request_type="GET",
            url=self.urls["carrier_services_integrations"].format(
                carrierCode=carrier_code,
                integration_code=integration_code,
            ),
        )
        return res.json()

    def create_shipment(self, vals):
        res = self._send_api_request(
            request_type="POST", url=self.urls["create_shipment"], data=vals
        )
        return res.json()

    def delete_shipment(self, deliverea_reference):
        self._send_api_request(
            request_type="DELETE",
            url=self.urls["delete_shipment"].format(
                delivereaReference=deliverea_reference
            ),
        )
        return True

    def get_shipment_label(self, deliverea_reference):
        res = self._send_api_request(
            request_type="GET",
            url=self.urls["get_shipment_label"].format(
                delivereaReference=deliverea_reference,
            ),
        )
        return res.json()

    def create_return(self, vals):
        res = self._send_api_request(
            request_type="POST", url=self.urls["create_return"], data=vals
        )
        return res.json()

    def get_shipment_tracking(self, deliverea_reference):
        res = self._send_api_request(
            request_type="GET",
            url=self.urls["get_shipment_tracking"].format(
                delivereaReference=deliverea_reference
            ),
        )
        return res.json()

    def get_return_tracking(self, deliverea_reference):
        res = self._send_api_request(
            request_type="GET",
            url=self.urls["get_return_tracking"].format(
                delivereaReference=deliverea_reference
            ),
        )
        return res.json()
