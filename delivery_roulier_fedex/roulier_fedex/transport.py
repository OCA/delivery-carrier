#  Copyright (c) 2026 Groupe Voltaire
#  @author Emilie SOUTIRAS  <emilie.soutiras@groupevoltaire.com>
#  License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import json
import logging
import threading
import time

import requests
from roulier.exception import CarrierError
from roulier.transport import RequestsTransport

from .constants import REQUEST_TIMEOUT, TOKEN_ENDPOINT, TOKEN_EXPIRY_MARGIN

_logger = logging.getLogger(__name__)

_token_cache = {}
_token_lock = threading.Lock()


class FedexTransport(RequestsTransport):
    def _get_base_url(self):
        if self.config.is_test:
            return self.config.base_test_url
        return self.config.base_url

    def _get_requests_url(self, payload=None):
        return self._get_base_url() + self.config.endpoint

    def before_ws_call_transform_payload(self, payload):
        return json.dumps(payload["body"])

    def _get_requests_headers(self, payload=None):
        return {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-locale": "en_US",
            "Authorization": "Bearer %s" % self._get_access_token(payload["auth"]),
        }

    def send_request(self, body, url, auth=None, headers=None, **kwargs):
        return requests.request(
            self.config.http_method,
            url,
            headers=headers,
            data=body,
            timeout=REQUEST_TIMEOUT,
        )

    def _token_cache_key(self, auth):
        return (self._get_base_url(), auth["login"])

    def _get_access_token(self, auth):
        key = self._token_cache_key(auth)
        with _token_lock:
            token, expires_at = _token_cache.get(key, (None, 0))
            if token and expires_at > time.time():
                return token
            response = requests.post(
                self._get_base_url() + TOKEN_ENDPOINT,
                data={
                    "grant_type": "client_credentials",
                    "client_id": auth["login"],
                    "client_secret": auth["password"],
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=REQUEST_TIMEOUT,
            )
            if response.status_code != 200:
                self._handle_errors(response)
            content = response.json()
            _token_cache[key] = (
                content["access_token"],
                time.time()
                + int(content.get("expires_in", 3600))
                - TOKEN_EXPIRY_MARGIN,
            )
            return content["access_token"]

    def _invalidate_token(self, response):
        auth = (self.config.roulier_input or {}).get("auth") or {}
        if auth.get("login"):
            with _token_lock:
                _token_cache.pop(self._token_cache_key(auth), None)

    def _handle_errors(self, response):
        try:
            fedex_errors = response.json().get("errors") or []
        except ValueError:
            fedex_errors = []
        errors = [
            {
                "id": error.get("code") or "unknown_%d" % response.status_code,
                "message": error.get("message") or response.reason,
            }
            for error in fedex_errors
        ] or [
            {
                "id": "unspecified_%d" % response.status_code,
                "message": response.reason,
            }
        ]
        raise CarrierError(response, errors)

    def _handle_success(self, response):
        return {"body": response.json(), "response": response}

    def handle_200(self, response):
        return self._handle_success(response)

    def handle_2XX(self, response):
        return self._handle_success(response)

    def handle_401(self, response):
        self._invalidate_token(response)
        return self._handle_errors(response)

    def handle_4XX(self, response):
        return self._handle_errors(response)

    def handle_500(self, response):
        return self._handle_errors(response)

    def handle_5XX(self, response):
        return self._handle_errors(response)
