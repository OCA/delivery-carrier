# Copyright 2025 Tecnativa - Víctor Martínez
# Copyright 2026 Acysos S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import json
import logging

import requests

from odoo import _, fields
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_round

from . import dachser_master_data as _dmd
from .dachser_master_data import (
    DACHSER_SHIPMENT_STATUS,
    map_dachser_status_to_delivery_state,
)

DACHSER_DEFAULT_API_URL = getattr(
    _dmd,
    "DACHSER_DEFAULT_API_URL",
    getattr(
        _dmd, "DACHSER_DEFAULT_BASE_URL", "https://api-gateway.dachser.com/rest/v2"
    ),
)

_logger = logging.getLogger(__name__)


class DachserRequest:
    """REST/JSON client for DACHSER Business Integration APIs v2."""

    def __init__(self, carrier):
        self.carrier_id = carrier
        self.carrier = carrier
        self.env = carrier.env
        self.timeout = 60
        self.division = self.carrier_id.dachser_division or "T"
        self.product = (
            self.carrier_id._dachser_get_product_code()
            if hasattr(self.carrier_id, "_dachser_get_product_code")
            else self.carrier_id[f"dachser_product_{self.division.lower()}"]
        )
        self.term = (
            self.carrier_id._dachser_get_term_code()
            if hasattr(self.carrier_id, "_dachser_get_term_code")
            else self.carrier_id.dachser_term
        )
        packaging_f_name = f"dachser_packaging_{self.division.lower()}"
        self.packaging = (
            self.carrier_id[packaging_f_name]
            if packaging_f_name in self.carrier_id._fields
            and self.carrier_id[packaging_f_name]
            else (self.carrier_id.dachser_default_packaging_code or "EU")
        )
        self.default_packaging = (
            self.carrier_id.dachser_default_packaging_id
            or self.carrier_id.dachser_default_package_type_id
        )
        base_url = self._get_base_url()
        basket = self.carrier_id.dachser_basket or "sent"
        self.urls = {
            "rate_shipment": f"{base_url}/quotations",
            "shipment": f"{base_url}/transportorders/{basket}",
            "tracking": f"{base_url}/shipmentstatus",
            "cancel": f"{base_url}/transportorders",
        }

    def _get_base_url(self):
        url = (
            (self.carrier.dachser_api_url or DACHSER_DEFAULT_API_URL)
            .strip()
            .rstrip("/")
        )
        if "://api.dachser.com" in url:
            url = url.replace("://api.dachser.com", "://api-gateway.dachser.com")
        if not url.endswith("/rest/v2"):
            if url.endswith("/rest"):
                url = f"{url}/v2"
            else:
                url = f"{url}/rest/v2"
        return url

    def _get_api_key(self):
        carrier = self.carrier.sudo()
        if carrier.prod_environment:
            api_key = (
                carrier.dachser_api_key_prod
                or carrier.dachser_api_key
                or carrier.dachser_api_key_test
            )
        else:
            api_key = (
                carrier.dachser_api_key_test
                or carrier.dachser_api_key
                or carrier.dachser_api_key_prod
            )
        if (
            not api_key
            and carrier.company_id
            and hasattr(carrier.company_id, "dachser_api_key")
        ):
            api_key = carrier.company_id.dachser_api_key
        if not api_key:
            env_name = _("Production") if carrier.prod_environment else _("Test")
            raise UserError(
                _(
                    "Missing Dachser API Key (X-API-Key) for %(env)s environment "
                    "on delivery method '%(carrier)s'."
                )
                % {"env": env_name, "carrier": self.carrier.name}
            )
        return api_key.strip()

    def _get_headers(self, lang=None):
        api_key = self._get_api_key()
        accept_lang = (lang or self.carrier.env.user.lang or "es_ES").replace("_", "-")
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "X-API-Key": api_key,
            "Accept-Language": accept_lang,
        }
        client_id = self.carrier.sudo().dachser_client_id
        if (
            not client_id
            and self.carrier.company_id
            and hasattr(self.carrier.company_id, "dachser_api_secret")
        ):
            client_id = self.carrier.company_id.dachser_api_secret
        if client_id:
            headers["X-IBM-Client-Id"] = client_id.strip()
        return headers

    def _format_error_message(self, response):
        status = response.status_code
        try:
            data = response.json()
        except Exception:
            data = None

        if isinstance(data, dict):
            msg = (
                data.get("message")
                or data.get("error")
                or data.get("httpMessage")
                or ""
            )
            details = data.get("details") or data.get("errors") or []
            if isinstance(details, list) and details:
                details_str = "\n- ".join(str(d) for d in details)
                return f"[HTTP {status}] {msg}\n- {details_str}".strip()
            if msg:
                return f"[HTTP {status}] {msg}"

        if status == 401:
            return _(
                "[HTTP 401 Unauthorized] The provided X-API-Key token is invalid "
                "or not subscribed to this Dachser web service."
            )
        if status == 429:
            return _(
                "[HTTP 429 Too Many Requests] The rate or burst limit per second/day "
                "has been exceeded for this Dachser API token."
            )
        text = (response.text or "").strip()
        return f"[HTTP {status}] {text[:500] or getattr(response, 'reason', '')}"

    def _request(
        self,
        method,
        endpoint,
        params=None,
        json_payload=None,
        lang=None,
        raise_on_error=True,
    ):
        url = (
            endpoint
            if endpoint.startswith("http")
            else f"{self._get_base_url()}/{endpoint.lstrip('/')}"
        )
        headers = self._get_headers(lang=lang)
        log_headers = dict(headers)
        if "X-API-Key" in log_headers and len(log_headers["X-API-Key"]) > 6:
            log_headers["X-API-Key"] = (
                log_headers["X-API-Key"][:4] + "***" + log_headers["X-API-Key"][-2:]
            )

        req_dump = {
            "method": method.upper(),
            "url": url,
            "params": params or {},
            "headers": log_headers,
            "body": json_payload,
        }
        self.carrier.log_xml(
            json.dumps(req_dump, indent=2, ensure_ascii=False),
            f"dachser_request_{endpoint}",
        )

        try:
            response = requests.request(
                method=method.upper(),
                url=url,
                params=params,
                json=json_payload,
                headers=headers,
                timeout=self.timeout,
            )
        except requests.exceptions.Timeout as tmo:
            err_msg = _("Timeout: the server did not reply within %ss") % self.timeout
            self.carrier.log_xml(str(tmo), f"dachser_error_{endpoint}")
            if raise_on_error:
                raise UserError(err_msg) from tmo
            return {"_error": True, "status_code": 0, "error_message": err_msg}
        except requests.exceptions.RequestException as exc:
            err_msg = _("Connection error with Dachser API (%(url)s): %(error)s") % {
                "url": url,
                "error": exc,
            }
            self.carrier.log_xml(str(exc), f"dachser_error_{endpoint}")
            if raise_on_error:
                raise UserError(err_msg) from exc
            return {"_error": True, "status_code": 0, "error_message": err_msg}

        resp_text = response.text or ""
        log_body = resp_text
        try:
            parsed = (
                response.json()
                if (resp_text or getattr(response, "content", None))
                else {}
            )
            if (
                isinstance(parsed, dict)
                and parsed.get("label")
                and len(str(parsed["label"])) > 200
            ):
                log_copy = dict(parsed)
                log_copy["label"] = f"<Base64 Label ({len(parsed['label'])} chars)>"
                log_body = json.dumps(log_copy, indent=2, ensure_ascii=False)
        except Exception:
            parsed = None

        self.carrier.log_xml(
            f"Status: {response.status_code}\n{log_body}",
            f"dachser_response_{endpoint}",
        )

        if response.status_code in (200, 201, 202, 204, 206):
            if response.status_code == 204 and parsed is None:
                return {"_status_code": response.status_code}
            if parsed is not None:
                if isinstance(parsed, dict):
                    parsed["_status_code"] = response.status_code
                return parsed
            return {"_status_code": response.status_code, "raw": resp_text}

        error_message = self._format_error_message(response)
        if raise_on_error:
            raise UserError(_("Dachser API Error:\n%s") % error_message)
        return {
            "_error": True,
            "status_code": response.status_code,
            "error_message": error_message,
            "data": parsed,
        }

    # -------------------------------------------------------------------------
    # OCA Legacy Helper Methods (Backward-Compatible Interface)
    # -------------------------------------------------------------------------
    def _send_api_request(self, request_type, url, data=None):
        data = data if data else {}
        result = {}
        headers = self._get_headers()
        try:
            if request_type in ("GET", "POST", "DELETE"):
                res = requests.request(
                    method=request_type,
                    url=url,
                    headers=headers,
                    params=data if request_type == "GET" else None,
                    json=data if request_type in ("POST", "DELETE") and data else None,
                    timeout=self.timeout,
                )
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
        except UserError:
            raise
        except Exception as e:
            err_detail = f"{e}\n{result}" if result else str(e)
            raise UserError(err_detail) from e
        return res

    def _prepare_quotation_data(self, order):
        partner_shipping = order.partner_shipping_id or order.partner_id
        transport_date = (
            order.expected_date.strftime("%Y-%m-%d")
            if getattr(order, "expected_date", False)
            else fields.Date.to_string(fields.Date.context_today(self.carrier_id))
        )
        return {
            "transportOrder": {
                "transportDate": transport_date,
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
                            )
                            or 1,
                            "unit": "KG",
                        },
                    }
                    for line in order.order_line.filtered(
                        lambda x: not x.display_type and not x.is_delivery
                    )
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
        streets = [partner.street] if partner.street else ["No street"]
        if partner.street2:
            streets.append(partner.street2)
        default_pkg = self.default_packaging
        return {
            "transportDate": fields.Datetime.now().strftime("%Y-%m-%d"),
            "division": self.division,
            "product": self.product,
            "term": self.term,
            "consignee": {
                "names": [partner.name],
                "addressInformation": {
                    "streets": streets[:1],
                    "city": partner.city,
                    "postalCode": partner.zip,
                    "countryCode": partner.country_id.code,
                },
            },
            "references": [{"code": "100", "value": picking.name[:35]}],
            "transportOrderLines": [
                {
                    "quantity": picking.number_of_packages
                    or picking.dachser_packages_qty
                    or 1,
                    "packaging": self.packaging,
                    "content": (
                        picking.dachser_content_override
                        or (
                            picking.move_ids_without_package[:1].description_picking
                            if picking.move_ids_without_package
                            else self.carrier_id.dachser_default_content
                        )
                        or "Goods"
                    )[:20],
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
                        "length": default_pkg.packaging_length if default_pkg else 120,
                        "width": default_pkg.width if default_pkg else 80,
                        "height": default_pkg.height if default_pkg else 120,
                        "unit": "CM",
                        "volume": {
                            "amount": getattr(picking, "volume", 0.0) or 0.01,
                            "unit": "M3",
                        },
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
        if response.status_code in (200, 201):
            response_json = response.json()
            res["tracking_number"] = (
                response_json.get("id") or (response_json.get("ssccs") or [False])[0]
            )
            res["label"] = response_json.get("label")
            res["ssccs"] = response_json.get("ssccs") or []
            res["state"] = response_json.get("state") or "sent"
        else:
            raise UserError(
                response.json().get("message", _("Error sending shipment to Dachser."))
            )
        return res

    def cancel_shipping(self, picking_ref):
        cancel_url = self.urls["cancel"]
        response = self._send_api_request(
            request_type="DELETE",
            url=f"{cancel_url}/{picking_ref}",
        )
        return True if response.status_code in (200, 204) else False

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
            "raw_json": False,
        }
        if response.status_code == 200:
            payload = response.json()
            res["raw_json"] = payload
            # Support both OCA dict {"shipments": [...]} and Swagger v2 list [...]
            if isinstance(payload, dict) and "shipments" in payload:
                shipment = payload["shipments"][-1] if payload["shipments"] else {}
                for status in shipment.get("status", []):
                    event_obj = status.get("event") or status
                    event_code = str(event_obj.get("code") or "")
                    event_description = event_obj.get("description") or ""
                    status_date = status.get("statusDate") or status.get("date") or ""
                    res["tracking_events"].append(
                        {
                            "statusDate": status_date,
                            "code": event_code,
                            "description": event_description,
                        }
                    )
                    if status.get("statusSequence") == 1 or not res["tracking_state"]:
                        res["tracking_state"] = event_description
                        res["delivery_state"] = DACHSER_SHIPMENT_STATUS.get(
                            event_code,
                            map_dachser_status_to_delivery_state(
                                event_code, event_description
                            ),
                        )
                res["tracking_events"] = res["tracking_events"][::-1]
            elif isinstance(payload, list) and payload:
                shipment = payload[0] or {}
                status_block = shipment.get("status")
                status_list = (
                    status_block
                    if isinstance(status_block, list)
                    else ([status_block] if isinstance(status_block, dict) else [])
                )
                for status in status_list:
                    event_code = str(status.get("code") or "")
                    event_description = status.get("description") or ""
                    status_date = status.get("date") or status.get("statusDate") or ""
                    res["tracking_events"].append(
                        {
                            "statusDate": status_date,
                            "code": event_code,
                            "description": event_description,
                            "location": status.get("location") or "",
                        }
                    )
                if res["tracking_events"]:
                    latest = res["tracking_events"][-1]
                    res["tracking_state"] = latest["description"]
                    res["delivery_state"] = map_dachser_status_to_delivery_state(
                        latest["code"], latest["description"]
                    )
        return res

    # -------------------------------------------------------------------------
    # 1. Transport Orders API (/rest/v2/transportorders)
    # -------------------------------------------------------------------------
    def create_transport_order(self, basket, payload, lang=None):
        """POST /rest/v2/transportorders/{basket}"""
        return self._request(
            "POST",
            f"transportorders/{basket}",
            json_payload=payload,
            lang=lang,
        )

    def send_transport_order(
        self, order_id, label_format="P", label_types=None, font_file_name=None
    ):
        """POST /rest/v2/transportorders/{id}/send"""
        params = {"label-format": label_format or "P"}
        if label_types:
            params["label-types"] = (
                ",".join(label_types) if isinstance(label_types, list) else label_types
            )
        if label_format == "Z" and font_file_name:
            params["font-file-name"] = font_file_name
        return self._request(
            "POST",
            f"transportorders/{int(order_id)}/send",
            params=params,
        )

    def get_transport_order_labels(
        self, order_id, label_format="P", label_types=None, font_file_name=None
    ):
        """POST /rest/v2/transportorders/{id}/labels"""
        params = {"label-format": label_format or "P"}
        if label_types:
            params["label-types"] = (
                ",".join(label_types) if isinstance(label_types, list) else label_types
            )
        if label_format == "Z" and font_file_name:
            params["font-file-name"] = font_file_name
        return self._request(
            "POST",
            f"transportorders/{int(order_id)}/labels",
            params=params,
        )

    def delete_transport_order(self, order_id, raise_on_error=True):
        """DELETE /rest/v2/transportorders/{id}"""
        return self._request(
            "DELETE",
            f"transportorders/{order_id}",
            raise_on_error=raise_on_error,
        )

    def list_transport_orders(self, basket=None, date_from=None, date_to=None):
        """GET /rest/v2/transportorders or /rest/v2/transportorders/{basket}"""
        endpoint = f"transportorders/{basket}" if basket else "transportorders"
        params = {}
        if date_from:
            params["date-from"] = str(date_from)
        if date_to:
            params["date-to"] = str(date_to)
        return self._request("GET", endpoint, params=params)

    def get_transfer_list(self, order_date, order_group=None, lang=None):
        """GET /rest/v2/transferlists/{orderdate}"""
        params = {}
        if order_group:
            params["order-group"] = str(order_group).strip()
        return self._request(
            "GET",
            f"transferlists/{order_date}",
            params=params or None,
            lang=lang,
        )

    get_transfer_lists = get_transfer_list

    # -------------------------------------------------------------------------
    # 2. Standalone Label API (/rest/v2/labels)
    # -------------------------------------------------------------------------
    def generate_standalone_label(self, payload, lang=None):
        """POST /rest/v2/labels"""
        return self._request(
            "POST",
            "labels",
            json_payload=payload,
            lang=lang,
        )

    get_standalone_labels = generate_standalone_label

    # -------------------------------------------------------------------------
    # 3. Quotations & Freight Costs API (/rest/v2/quotations, /rest/v2/freightcosts)
    # -------------------------------------------------------------------------
    def get_quotation(self, payload, lang=None, raise_on_error=True):
        """POST /rest/v2/quotations"""
        return self._request(
            "POST",
            "quotations",
            json_payload=payload,
            lang=lang,
            raise_on_error=raise_on_error,
        )

    def get_freight_costs(
        self, tracking_number, customer_id=None, lang=None, raise_on_error=True
    ):
        """GET /rest/v2/freightcosts?tracking-number=..."""
        params = {"tracking-number": str(tracking_number).strip()}
        if customer_id:
            params["customer-id"] = str(customer_id).strip()
        return self._request(
            "GET",
            "freightcosts",
            params=params,
            lang=lang,
            raise_on_error=raise_on_error,
        )

    # -------------------------------------------------------------------------
    # 4. Track & Trace and POD APIs (/rest/v2/shipmentstatus, /shipmenthistory, /pods)
    # -------------------------------------------------------------------------
    def get_shipment_status(
        self, tracking_number, customer_id=None, lang=None, raise_on_error=True
    ):
        """GET /rest/v2/shipmentstatus"""
        params = {"tracking-number": str(tracking_number).strip()}
        if customer_id:
            params["customer-id"] = str(customer_id).strip()
        return self._request(
            "GET",
            "shipmentstatus",
            params=params,
            lang=lang,
            raise_on_error=raise_on_error,
        )

    def get_shipment_history(
        self, tracking_number, customer_id=None, lang=None, raise_on_error=True
    ):
        """GET /rest/v2/shipmenthistory"""
        params = {"tracking-number": str(tracking_number).strip()}
        if customer_id:
            params["customer-id"] = str(customer_id).strip()
        return self._request(
            "GET",
            "shipmenthistory",
            params=params,
            lang=lang,
            raise_on_error=raise_on_error,
        )

    def get_pod(self, tracking_number, customer_id=None, raise_on_error=True):
        """GET /rest/v2/pods"""
        params = {"tracking-number": str(tracking_number).strip()}
        if customer_id:
            params["customer-id"] = str(customer_id).strip()
        return self._request(
            "GET",
            "pods",
            params=params,
            raise_on_error=raise_on_error,
        )

    # -------------------------------------------------------------------------
    # 5. Routing & SSCC Pool APIs (/rest/v2/routings, /rest/v2/ssccs)
    # -------------------------------------------------------------------------
    def get_routing(
        self,
        branch_id=None,
        country_code=None,
        postal_code=None,
        division="T",
        product="Y",
        shipment_date=None,
        forwarder_id=None,
        consignor_country=None,
        consignor_zip=None,
        consignor_city=None,
        consignee_country=None,
        consignee_zip=None,
        consignee_city=None,
        raise_on_error=True,
    ):
        """GET /rest/v2/routings"""
        eff_branch = forwarder_id or branch_id or "193"
        eff_country = consignee_country or country_code or "ES"
        eff_zip = consignee_zip or postal_code or "00000"
        params = {
            "branch-id": str(eff_branch).strip(),
            "division": division or "T",
            "country-code": str(eff_country).strip().upper(),
            "postal-code": str(eff_zip).strip(),
        }
        if product:
            params["product"] = str(product).strip()
        if shipment_date:
            params["shipment-date"] = str(shipment_date).strip()
        if consignee_city:
            params["city"] = str(consignee_city).strip()
        return self._request(
            "GET",
            "routings",
            params=params,
            raise_on_error=raise_on_error,
        )

    def get_ssccs(self, count=1, use_prefix=True):
        """POST /rest/v2/ssccs"""
        payload = {
            "count": min(max(int(count), 1), 100),
            "usePrefix": bool(use_prefix),
        }
        return self._request("POST", "ssccs", json_payload=payload)
