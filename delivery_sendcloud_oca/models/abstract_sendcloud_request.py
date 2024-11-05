# Copyright 2024 Onestein (<https://www.onestein.nl>)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl)

import time
from json.decoder import JSONDecodeError
from urllib.parse import urlparse

import requests

from odoo import SUPERUSER_ID, _, api, models, registry
from odoo.exceptions import UserError

TIMEOUT = 60


class SendcloudRequest(models.AbstractModel):
    _name = "sendcloud.request"
    _description = "Sendcloud Request Abstract"

    def _param_web_base_url(self):
        base_url = self.env["ir.config_parameter"].get_param("web.base.url")
        parsed_url = urlparse(base_url)
        return parsed_url._replace(scheme="https").geturl()

    def _base_panel_url(self):
        return "https://panel.sendcloud.sc/api/v2"

    def _default_integration_webhook(self, company_id):
        webhook = "/shop/sendcloud_integration_webhook"
        return f"{webhook}/{company_id}"

    def _do_auth_request(self, type_request, url, data=None):
        self.ensure_one()
        auth = (self.public_key, self.secret_key)
        return self._do_request(type_request, url, data, auth=auth)

    def _do_request(self, type_request, url, data=None, auth=None, headers=None):
        self.ensure_one()
        start_time = time.time()
        resp = requests.Response()
        try:
            if type_request == "POST":
                resp = requests.post(
                    url=url, json=data, auth=auth, headers=headers, timeout=TIMEOUT
                )
            elif type_request == "GET":
                resp = requests.get(url=url, params=data, auth=auth, timeout=TIMEOUT)
            elif type_request == "PUT":
                resp = requests.put(url=url, json=data, auth=auth, timeout=TIMEOUT)
        except requests.ConnectionError as CE:
            raise UserError(
                _("Sendcloud: server not reachable, try again later")
            ) from CE
        except requests.Timeout as TO:
            raise UserError(
                _("Sendcloud timeout: the server didn't reply within 30s")
            ) from TO
        except requests.HTTPError as HE:
            error_msg = resp.json().get("error", {}).get("message", "")
            raise UserError(_("Sendcloud: %s") % error_msg or resp.text) from HE

        # Handle request limiting (retry after one second)
        if resp.status_code == 429:
            time.sleep(1)
            return self._do_request(
                type_request, url, data=data, auth=auth, headers=headers
            )

        end_time = time.time()
        response_time = end_time - start_time
        with registry(self.env.cr.dbname).cursor() as new_cr:
            # Create a new environment with new cursor database
            new_env = api.Environment(new_cr, SUPERUSER_ID, self.env.context)
            self.with_env(new_env)._log_response_in_action(
                resp, type_request, url, str(data), response_time
            )
        err_msg = self._check_response_ok(resp)
        if err_msg:
            err_msg = err_msg + "\n" + _("Request: %s") % data
            raise UserError(err_msg)
        return resp

    def _check_response_ok(self, resp):
        if self.env.context.get("skip_sendcloud_check_response"):
            return ""
        ok_status = self._ok_response_status()
        err_msg = ""
        if resp.status_code not in ok_status:
            err_msg = _("Sendcloud: %(reason)s (error code %(status_code)s)") % (
                {"reason": resp.reason, "status_code": resp.status_code}
            )
            if resp.status_code == 500:
                err_msg += "\n" + _("Internal server error.")
            else:
                resp_dict = resp.json()
                if resp_dict.get("error"):
                    err_msg += "\n" + resp_dict["error"].get("message", "")
                elif resp_dict.get("message"):
                    err_msg += "\n" + resp_dict["message"]
        return err_msg

    def _ok_response_status(self):
        # 200: OK
        # 201: OK, eg.: creating/updating a list of shipments
        # 204: No Content, eg.: when deleting a shipment
        # 404: Not found, eg.: when deleting a parcel
        # 410: Happens when the parcel announcement has failed, the parcel
        # status contains id of 1002 and you try to cancel it.
        return self.env.context.get(
            "sendcloud_ok_response_status", (200, 204, 404, 410)
        )

    def _log_response_in_action(
        self, resp, type_request, url, sent_payload, response_time
    ):
        self.ensure_one()
        try:
            decoded_content = resp.content.decode()
        except Exception:
            decoded_content = "Byte content"
        if resp.status_code == 401 and not self.env.context.get("skip_raise_error_401"):
            error_msg = resp.json().get("error", {}).get("message", "")
            raise UserError(_("Sendcloud: %s") % error_msg or resp.text)
        company = self.company_id
        self.env["sendcloud.action"].create(
            {
                "company_id": company.id,
                "sendcloud_integration_id": self.id,
                "message_type": "sent",
                "exitcode": str(resp.status_code) if resp.status_code else False,
                "action": f"{type_request}: {url}",
                "message": decoded_content,
                "response_time": response_time,
                "sent_payload": sent_payload or False,
                "model": self._name,
                "resid": self.id,
            }
        )

    def _iterate_pagination(self, response, urlpath, list_name):
        res = response.get(list_name)
        next_response = response.get("next")
        while next_response:
            parsed_next = urlparse(response.get("next"))
            response = self._get_panel_request(urlpath + "?" + parsed_next.query)
            res += response.get(list_name)
            next_response = response.get("next")
        return res

    def _get_request(self, url, params=None):
        if params:
            res = self._do_auth_request("GET", url, data=params)
        else:
            res = self._do_auth_request("GET", url)
        return self._format_response(res)

    def _post_request(self, url, data=None):
        res = self._do_auth_request("POST", url, data)
        return self._format_response(res)

    def _put_request(self, url, data):
        res = self._do_auth_request("PUT", url, data)
        return self._format_response(res)

    def _format_response(self, res):
        """
        The HTTP 204 No Content success status response code indicates that the
        request has succeeded, but that the reply message is empty.
        """
        if res.status_code == 204:
            return {}
        try:
            res = res.json()
        except JSONDecodeError:
            # If it is not possible get json then
            # use response exception message
            return {
                "error": {
                    "code": "JSONDecodeError",
                    "message": ("Unable to read response message"),
                }
            }
        return res

    def _get_panel_request(self, url, params=None):
        url = self._base_panel_url() + url
        return self._get_request(url, params)

    def _post_panel_request(self, url, data=None):
        url = self._base_panel_url() + url
        return self._post_request(url, data)

    def _put_panel_request(self, url, data):
        url = self._base_panel_url() + url
        return self._put_request(url, data)

    def get_sender_address(self):
        response = self._get_panel_request("/user/addresses/sender")
        return response.get("sender_addresses")

    def get_user_invoices(self):
        response = self._get_panel_request("/user/invoices")
        return response.get("invoices")

    def get_user_invoice(self, code):
        response = self._get_panel_request("/user/invoices/%s" % code)
        return response.get("invoice")

    def get_integrations(self):
        return self._get_panel_request("/integrations")

    def get_shipping_methods(self, params):
        response = self._get_panel_request("/shipping_methods", params)
        return response.get("shipping_methods")

    def get_shipping_method(self, code, params):
        response = self._get_panel_request("/shipping_methods/%s" % code, params)
        return response.get("shipping_method")

    def get_parcels(self):
        urlpath = "/parcels"
        response = self._get_panel_request(urlpath)
        return self._iterate_pagination(response, urlpath, "parcels")

    def get_parcel(self, code):
        response = self._get_panel_request("/parcels/%s" % code)
        return response.get("parcel")

    def get_parcels_statuses(self):
        return self._get_panel_request("/parcels/statuses")

    def get_brands(self):
        urlpath = "/brands"
        response = self._get_panel_request(urlpath)
        return self._iterate_pagination(response, urlpath, "brands")

    def create_parcels(self, post_data):
        return self._post_panel_request("/parcels", post_data)

    def create_shipments(self, integration_code, vals_list):
        post_data = []
        for vals in vals_list:
            shipping_method = vals["shipment"]["id"]
            vals.update(
                {
                    "shipping_method": shipping_method,
                }
            )
            post_data += [vals]
        url = "/integrations/%s/shipments" % integration_code
        return self._post_panel_request(url, post_data)

    def delete_shipments(self, integration_id, post_data):
        url = "/integrations/%s/shipments/delete" % integration_id
        return self._post_panel_request(url, post_data)

    def get_parcel_label(self, label_printer_url):
        res = self._do_auth_request("GET", label_printer_url)
        return res.content

    def get_return_portal_url(self, code):
        return self._get_panel_request("/parcels/%d/return_portal_url" % code)

    def get_parcel_document(self, link):
        res = self._do_auth_request("GET", link)
        return res.content

    def cancel_parcel(self, code):
        self = self.with_context(skip_sendcloud_check_response=True)
        return self._post_panel_request("/parcels/%s/cancel" % code)

    def update_integration(self, code, data):
        return self._put_panel_request("/integrations/%s" % code, data)

    def get_returns(self):
        urlpath = "/returns"
        response = self._get_panel_request(urlpath)
        return self._iterate_pagination(response, urlpath, "returns")

    def get_return(self, code):
        return self._get_panel_request("/returns/%s" % code)

    def get_return_portal_settings(self, domain_brand, language=""):
        url = "/brand/%s/return-portal" % domain_brand
        if language:
            url += "?language=" + language
        url = self._base_panel_url() + url
        res = self._do_request("GET", url)
        return res.json()

    def get_return_portal_outgoing_parcel(self, domain_brand, params):
        url = "/brand/%s/return-portal/outgoing" % domain_brand
        url = self._base_panel_url() + url
        res = self._do_request("GET", url, data=params)
        return res.json()

    def create_return_portal_incoming_parcel(self, domain_brand, payload, headers):
        url = "/brand/%s/return-portal/incoming" % domain_brand
        url = self._base_panel_url() + url
        res = self._do_request("POST", url, data=payload, headers=headers)
        return res.json()
