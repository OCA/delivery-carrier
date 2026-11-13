# Copyright 2025 Tecnativa - Víctor Martínez
# Copyright 2026 Acysos S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import json
import logging
import math

import requests

from odoo import _, fields
from odoo.exceptions import UserError
from odoo.tools import html2plaintext

from .dachser_master_data import (
    DACHSER_DEFAULT_API_URL,
    DACHSER_INCOTERM_TO_TERM,
    map_dachser_status_to_delivery_state,
)

_logger = logging.getLogger(__name__)


class DachserRequest:
    """Client and payload builder for Dachser REST API v2
    (`https://api-gateway.dachser.com/rest/v2`).
    """

    def __init__(self, carrier):
        self.carrier_id = carrier
        self.env = carrier.env
        self.timeout = 60
        self.division = carrier.dachser_division or "T"
        product_field = f"dachser_product_{self.division.lower()}"
        self.product = carrier[product_field] or ("Y" if self.division == "T" else "N")
        packaging_field = f"dachser_packaging_{self.division.lower()}"
        self.packaging = carrier[packaging_field] or "EU"
        self.default_packaging = carrier.dachser_default_packaging_id
        # Dachser uses the same API Gateway URL for both test and prod environments
        self.base_url = DACHSER_DEFAULT_API_URL
        basket = carrier.dachser_basket or "sent"
        self.urls = {
            "rate_shipment": f"{self.base_url}/quotations",
            "shipment": f"{self.base_url}/transportorders/{basket}",
            "tracking": f"{self.base_url}/shipmentstatus",
            "cancel": f"{self.base_url}/transportorders",
        }

    # -------------------------------------------------------------------------
    # HTTP & Authentication Helpers
    # -------------------------------------------------------------------------
    def _get_api_key(self):
        api_key = self.carrier_id.sudo().dachser_api_key
        if not api_key:
            raise UserError(
                _("Missing Dachser API Key (X-API-Key) on delivery method '%s'.")
                % self.carrier_id.name
            )
        return api_key.strip()

    def _get_headers(self, lang=None):
        api_key = self._get_api_key()
        accept_lang = (lang or self.env.user.lang or "es_ES").replace("_", "-")
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "X-API-Key": api_key,
            "Accept-Language": accept_lang,
        }
        client_id = self.carrier_id.sudo().dachser_client_id
        if client_id:
            headers["X-IBM-Client-Id"] = client_id.strip()
        return headers

    def _format_error_message(self, response):
        status = response.status_code
        try:
            data = response.json()
        except ValueError:
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
                "[HTTP 429 Too Many Requests] The rate or burst limit "
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
            else f"{self.base_url}/{endpoint.lstrip('/')}"
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
        self.carrier_id.log_xml(
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
            self.carrier_id.log_xml(str(tmo), f"dachser_error_{endpoint}")
            if raise_on_error:
                raise UserError(err_msg) from tmo
            return {"_error": True, "status_code": 0, "error_message": err_msg}
        except requests.exceptions.RequestException as exc:
            err_msg = _("Connection error with Dachser API (%(url)s): %(error)s") % {
                "url": url,
                "error": exc,
            }
            self.carrier_id.log_xml(str(exc), f"dachser_error_{endpoint}")
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
        except ValueError:
            parsed = None

        self.carrier_id.log_xml(
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
    # Data & Payload Preparation Helpers (_prepare_*)
    # -------------------------------------------------------------------------
    @staticmethod
    def _split_text(text, max_len=30, max_items=3):
        """Split a text string into up to `max_items` chunks of `max_len` chars."""
        cleaned = " ".join((text or "").strip().split())
        if not cleaned:
            return []
        chunks = []
        remaining = cleaned
        while remaining and len(chunks) < max_items:
            if len(remaining) <= max_len:
                chunks.append(remaining)
                break
            cut = remaining.rfind(" ", 0, max_len + 1)
            if cut <= 0:
                cut = max_len
            chunks.append(remaining[:cut].strip())
            remaining = remaining[cut:].strip()
        return chunks

    def _convert_weight_to_kg(self, weight):
        """Convert a weight value from Odoo's default weight UoM to kilograms."""
        if not weight:
            return 0.0
        weight_uom = self.env[
            "product.template"
        ]._get_weight_uom_id_from_ir_config_parameter()
        kg_uom = self.env.ref("uom.product_uom_kgm", raise_if_not_found=False)
        if weight_uom and kg_uom and weight_uom != kg_uom:
            return weight_uom._compute_quantity(weight, kg_uom, round=False)
        return float(weight)

    def _convert_dimension_to_cm(self, dimension_value):
        """Convert a package dimension from Odoo's default length UoM to cm."""
        if not dimension_value:
            return 0
        length_uom = self.env[
            "product.template"
        ]._get_length_uom_id_from_ir_config_parameter()
        cm_uom = self.env.ref("uom.product_uom_cm", raise_if_not_found=False)
        if length_uom and cm_uom and length_uom != cm_uom:
            cm_val = length_uom._compute_quantity(dimension_value, cm_uom, round=False)
        else:
            cm_val = float(dimension_value)
        return max(1, int(round(cm_val)))

    def _get_term_code(self, order=None, picking=None):
        """Resolve Dachser 3-digit delivery term code (optionally from Incoterm)."""
        if self.carrier_id.dachser_use_order_incoterm:
            incoterm = False
            if picking and getattr(picking, "incoterm", False):
                incoterm = picking.incoterm
            elif (
                picking
                and picking.sale_id
                and getattr(picking.sale_id, "incoterm", False)
            ):
                incoterm = picking.sale_id.incoterm
            elif order and getattr(order, "incoterm", False):
                incoterm = order.incoterm
            if incoterm and incoterm.code in DACHSER_INCOTERM_TO_TERM:
                return DACHSER_INCOTERM_TO_TERM[incoterm.code]
        return self.carrier_id.dachser_term or "031"

    def _get_label_types_list(self):
        raw = self.carrier_id.dachser_label_types or "EAN"
        return [item.strip() for item in raw.split(",") if item.strip()]

    def _get_package_dimensions_cm(self, package_type=None):
        """Return (length_cm, width_cm, height_cm, packaging_code, unit_ldm)."""
        pkg_type = package_type or self.default_packaging
        shipper_code = (
            pkg_type.shipper_package_code
            if pkg_type
            and pkg_type.shipper_package_code
            and pkg_type.shipper_package_code != "default"
            else None
        )
        pkg_code = (
            (
                pkg_type.dachser_packaging_code
                if pkg_type and pkg_type.dachser_packaging_code
                else None
            )
            or shipper_code
            or self.packaging
            or "EU"
        )
        if (
            pkg_type
            and pkg_type.packaging_length
            and pkg_type.width
            and pkg_type.height
        ):
            l_cm = self._convert_dimension_to_cm(pkg_type.packaging_length)
            w_cm = self._convert_dimension_to_cm(pkg_type.width)
            h_cm = self._convert_dimension_to_cm(pkg_type.height)
        elif pkg_code == "EU":
            l_cm, w_cm, h_cm = 120, 80, 120
        elif pkg_code in ("EP", "DD", "HE", "HP"):
            l_cm, w_cm, h_cm = 80, 60, 100
        elif pkg_code == "IP":
            l_cm, w_cm, h_cm = 120, 100, 120
        else:
            l_cm, w_cm, h_cm = 60, 40, 40

        if pkg_code == "EU":
            unit_ldm = 0.4
        elif pkg_code in ("EP", "DD", "HE", "HP"):
            unit_ldm = 0.2
        elif pkg_code == "IP":
            unit_ldm = 0.5
        else:
            unit_ldm = round((l_cm / 100.0) * (w_cm / 100.0) / 2.4, 2)
        return l_cm, w_cm, h_cm, pkg_code, unit_ldm

    def _validate_partner(self, partner, picking=None):
        if not partner:
            raise UserError(
                _("Picking %s does not have a delivery address assigned.")
                % (picking.name if picking else "")
            )
        if not partner.country_id or not partner.zip or not partner.city:
            raise UserError(
                _(
                    "Consignee %s must have City, Postal Code, and Country "
                    "configured."
                )
                % partner.display_name
            )
        return partner

    def _prepare_partner_data(
        self, partner, include_id=False, is_consignor=False, minimal=False
    ):
        """Build `consignor` or `consignee` JSON block within Dachser API v2 limits."""
        carrier = self.carrier_id
        if is_consignor and include_id and carrier.dachser_consignor_id and minimal:
            payload = {"id": carrier.dachser_consignor_id.strip()}
            if carrier.dachser_consignor_gln:
                payload["gln"] = carrier.dachser_consignor_gln.strip()
            return payload

        commercial_name = (
            partner.commercial_partner_id.name or partner.name or "Customer"
        )
        names = self._split_text(commercial_name, max_len=30, max_items=2)
        if partner.name and partner.name != commercial_name and len(names) < 3:
            names.extend(
                self._split_text(partner.name, max_len=30, max_items=3 - len(names))
            )
        if not names:
            names = ["Customer"]

        full_street = (
            " ".join(filter(None, [partner.street, partner.street2])).strip()
            or "No street"
        )
        street_chunks = self._split_text(full_street, max_len=30, max_items=3)
        primary_street = street_chunks[0] if street_chunks else "No street"
        supplement_parts = street_chunks[1:] if len(street_chunks) > 1 else []
        if partner.phone or partner.mobile:
            supplement_parts.append(f"Tel: {(partner.mobile or partner.phone).strip()}")

        country_code = (
            partner.country_id.code or self.env.company.country_id.code or "ES"
        ).upper()
        postal_code = (partner.zip or "00000").strip()[:10]
        city = (partner.city or partner.state_id.name or "City").strip()[:30]
        lang_iso = (partner.lang or self.env.user.lang or "es_ES")[:2].lower()

        address_info = {
            "streets": [primary_street],
            "city": city,
            "postalCode": postal_code,
            "countryCode": country_code,
        }
        if supplement_parts:
            address_info["supplementInformation"] = " - ".join(supplement_parts)[:60]

        payload = {
            "language": lang_iso,
            "names": names[:3],
            "addressInformation": address_info,
        }
        if is_consignor:
            if include_id and carrier.dachser_consignor_id:
                payload["id"] = carrier.dachser_consignor_id.strip()
            if carrier.dachser_consignor_gln:
                payload["partnerGLN"] = carrier.dachser_consignor_gln.strip()
        else:
            if include_id and partner.dachser_partner_id:
                payload["id"] = partner.dachser_partner_id.strip()
            if partner.dachser_gln:
                payload["partnerGLN"] = partner.dachser_gln.strip()
        return payload

    def _prepare_transport_options(self, partner):
        """Build `transportOptions` for transport orders and quotations."""
        carrier = self.carrier_id
        tail_lift = bool(
            partner.dachser_tail_lift or carrier.dachser_delivery_tail_lift
        )
        notice_type = (
            partner.dachser_delivery_notice_type
            if partner.dachser_delivery_notice_type
            and partner.dachser_delivery_notice_type != "none"
            else carrier.dachser_delivery_notice_type
        )
        options = {
            "collectionOption": carrier.dachser_collection_option or "CN",
            "deliveryTailLift": tail_lift,
            "selfCollector": bool(carrier.dachser_self_collector),
            "frostProtected": bool(carrier.dachser_frost_protected),
        }
        if carrier.dachser_collection_time_from:
            options["collectionTimeFrom"] = carrier.dachser_collection_time_from.strip()
        if carrier.dachser_collection_time_to:
            options["collectionTimeTo"] = carrier.dachser_collection_time_to.strip()

        if notice_type and notice_type in ("AS", "AI", "TE", "SM", "EM", "AV"):
            notice_entry = {
                "type": notice_type if notice_type in ("AS", "AI") else "AS",
                "name": (
                    partner.name or partner.commercial_partner_id.name or "Contact"
                )[:30],
            }
            if partner.mobile:
                notice_entry["mobilePhone"] = partner.mobile.strip()[:25]
            if partner.phone:
                notice_entry["phone"] = partner.phone.strip()[:25]
            elif partner.mobile:
                notice_entry["phone"] = partner.mobile.strip()[:25]
            if partner.email:
                notice_entry["mail"] = partner.email.strip()[:60]
            options["deliveryNoticeOptions"] = [notice_entry]
        return options

    @staticmethod
    def _prepare_references(picking):
        """Build `references` list for Dachser (code 100 mandatory, max 35 chars)."""
        ref_100 = (picking.name or picking.origin or "SHIPMENT")[:35]
        refs = [{"code": "100", "value": ref_100}]
        if picking.sale_id and picking.sale_id.client_order_ref:
            refs.append({"code": "101", "value": picking.sale_id.client_order_ref[:35]})
        elif picking.origin and picking.origin != picking.name:
            refs.append({"code": "102", "value": picking.origin[:35]})
        return refs

    def _prepare_quotation_data(self, order):
        """Build payload for `POST /rest/v2/quotations`."""
        partner = order.partner_shipping_id or order.partner_id
        total_weight_kg = 0.0
        for line in order.order_line.filtered(
            lambda ol: not ol.is_delivery
            and not ol.display_type
            and ol.product_id.type in ("consu", "product")
        ):
            total_weight_kg += self._convert_weight_to_kg(
                (line.product_id.weight or 0.0) * line.product_uom_qty
            )
        if total_weight_kg <= 0.0:
            est_w = (
                order._get_estimated_weight()
                if hasattr(order, "_get_estimated_weight")
                else 0.0
            )
            total_weight_kg = max(1.0, self._convert_weight_to_kg(est_w) or 1.0)

        l_cm, w_cm, h_cm, pkg_code, unit_ldm = self._get_package_dimensions_cm()
        max_pkg_w = (
            self._convert_weight_to_kg(self.default_packaging.max_weight)
            if self.default_packaging and self.default_packaging.max_weight > 0
            else (
                700.0
                if pkg_code in ("EU", "PA", "IP", "EP", "DD", "HE", "HP")
                else 25.0
            )
        )
        packages_qty = (
            max(1, int(math.ceil(total_weight_kg / max_pkg_w))) if max_pkg_w > 0 else 1
        )
        unit_vol_m3 = (l_cm / 100.0) * (w_cm / 100.0) * (h_cm / 100.0)
        total_vol_m3 = max(0.01, round(unit_vol_m3 * packages_qty, 2))
        content_str = (self.carrier_id.dachser_default_content or "Goods")[:20]

        transport_order = {
            "transportDate": fields.Date.to_string(
                fields.Date.context_today(self.carrier_id)
            ),
            "division": self.division,
            "product": self.product,
            "term": self._get_term_code(order=order),
            "consignor": {
                "id": (self.carrier_id.dachser_consignor_id or "00000000").strip()
            },
            "consignee": self._prepare_partner_data(
                partner, include_id=False, is_consignor=False
            ),
            "transportOptions": self._prepare_transport_options(partner),
            "transportOrderLines": [
                {
                    "quantity": packages_qty,
                    "packaging": pkg_code,
                    "content": content_str,
                    "weight": {"weight": round(total_weight_kg, 2), "unit": "KG"},
                    "loadingMetre": round(unit_ldm * packages_qty, 2),
                    "measure": {
                        "length": l_cm,
                        "width": w_cm,
                        "height": h_cm,
                        "unit": "CM",
                        "volume": {"amount": total_vol_m3, "unit": "M3"},
                    },
                }
            ],
        }
        if order.name:
            transport_order["references"] = [{"code": "100", "value": order.name[:35]}]

        return {
            "logisticsType": self.carrier_id.dachser_logistics_type or "D",
            "saveQuotation": bool(self.carrier_id.dachser_save_quotation),
            "transportOrder": transport_order,
        }

    def _prepare_picking_lines(self, picking):
        """Build `transportOrderLines` and package count from physical packages
        (`move_line_ids.result_package_id`) or from picking totals.
        """
        default_desc = (
            picking.move_ids_without_package[:1].description_picking
            if picking.move_ids_without_package
            else False
        )
        content_str = (
            self.carrier_id.dachser_default_content or default_desc or "Goods"
        )[:20]
        packages = picking.move_line_ids.mapped("result_package_id")

        order_lines = []
        total_packages_qty = 0

        if packages:
            for pkg in packages:
                pkg_type = pkg.package_type_id or self.default_packaging
                l_cm, w_cm, h_cm, pkg_code, unit_ldm = self._get_package_dimensions_cm(
                    pkg_type
                )
                pkg_weight = getattr(pkg, "shipping_weight", 0.0) or getattr(
                    pkg, "weight", 0.0
                )
                pkg_weight_kg = self._convert_weight_to_kg(pkg_weight)
                if pkg_weight_kg <= 0.0:
                    moves_w = sum(
                        ml.product_id.weight * ml.quantity
                        for ml in picking.move_line_ids
                        if ml.result_package_id == pkg
                    )
                    pkg_weight_kg = max(1.0, self._convert_weight_to_kg(moves_w))

                vol_m3 = max(
                    0.01, round((l_cm / 100.0) * (w_cm / 100.0) * (h_cm / 100.0), 2)
                )
                total_packages_qty += 1
                order_lines.append(
                    {
                        "quantity": 1,
                        "packaging": pkg_code,
                        "content": content_str,
                        "weight": {
                            "weight": str(round(pkg_weight_kg, 2)),
                            "unit": "KG",
                        },
                        "loadingMetre": round(unit_ldm, 2),
                        "measure": {
                            "length": l_cm,
                            "width": w_cm,
                            "height": h_cm,
                            "unit": "CM",
                            "volume": {"amount": str(vol_m3), "unit": "M3"},
                        },
                    }
                )
        else:
            raw_weight = picking.shipping_weight or picking.weight or 0.0
            total_weight_kg = self._convert_weight_to_kg(raw_weight)
            if total_weight_kg <= 0.0:
                total_weight_kg = sum(
                    self._convert_weight_to_kg(
                        (m.product_id.weight or 0.0) * (m.quantity or m.product_uom_qty)
                    )
                    for m in picking.move_ids.filtered(lambda x: x.state != "cancel")
                )
            total_weight_kg = max(1.0, total_weight_kg)

            l_cm, w_cm, h_cm, pkg_code, unit_ldm = self._get_package_dimensions_cm()
            total_packages_qty = max(1, getattr(picking, "number_of_packages", 0) or 1)
            picking_vol = getattr(picking, "volume", 0.0) or 0.0
            unit_vol_m3 = (l_cm / 100.0) * (w_cm / 100.0) * (h_cm / 100.0)
            total_vol_m3 = (
                max(0.01, round(picking_vol, 2))
                if picking_vol > 0.0
                else max(0.01, round(unit_vol_m3 * total_packages_qty, 2))
            )
            order_lines.append(
                {
                    "quantity": total_packages_qty,
                    "packaging": pkg_code,
                    "content": content_str,
                    "weight": {"weight": str(round(total_weight_kg, 2)), "unit": "KG"},
                    "loadingMetre": round(unit_ldm * total_packages_qty, 2),
                    "measure": {
                        "length": l_cm,
                        "width": w_cm,
                        "height": h_cm,
                        "unit": "CM",
                        "volume": {"amount": str(total_vol_m3), "unit": "M3"},
                    },
                }
            )
        return total_packages_qty, order_lines

    def _get_shipper_partner(self, picking):
        return (
            picking.picking_type_id.warehouse_id.partner_id
            or picking.company_id.partner_id
            or self.env.company.partner_id
        )

    def _prepare_shipment_data(self, picking):
        """Build payload for `POST /rest/v2/transportorders/{basket}`."""
        partner = self._validate_partner(picking.partner_id, picking=picking)
        shipper_partner = self._get_shipper_partner(picking)
        ship_date = fields.Date.to_string(
            picking.scheduled_date.date()
            if picking.scheduled_date
            else fields.Date.context_today(self.carrier_id)
        )
        _packages_qty, order_lines = self._prepare_picking_lines(picking)
        carrier = self.carrier_id
        payload = {
            "transportDate": ship_date,
            "labelFormat": carrier.dachser_label_format or "P",
            "labelTypes": self._get_label_types_list(),
            "division": self.division,
            "product": self.product,
            "term": self._get_term_code(picking=picking),
            "forwarder": {"id": (carrier.dachser_forwarder_id or "193").strip()},
            "consignor": self._prepare_partner_data(
                shipper_partner,
                include_id=True,
                is_consignor=True,
                minimal=bool(carrier.dachser_consignor_id),
            ),
            "consignee": self._prepare_partner_data(
                partner, include_id=True, is_consignor=False
            ),
            "references": self._prepare_references(picking),
            "transportOrderLines": order_lines,
            "transportOptions": self._prepare_transport_options(partner),
        }
        if carrier.dachser_label_format == "Z" and carrier.dachser_font_file_name:
            payload["fontFileName"] = carrier.dachser_font_file_name.strip()
        if carrier.dachser_order_group:
            payload["orderGroup"] = carrier.dachser_order_group.strip()[:30]
        if picking.note:
            plain_note = html2plaintext(picking.note).strip()
            if plain_note:
                payload["texts"] = [{"code": "ZU", "value": plain_note[:70]}]
        return payload

    def _prepare_label_data(
        self, picking, is_return=False, ship_date=None, existing_ssccs=None
    ):
        """Build payload for `POST /rest/v2/labels` (standalone or return labels)."""
        partner = self._validate_partner(picking.partner_id, picking=picking)
        shipper_partner = self._get_shipper_partner(picking)
        eff_date = fields.Date.to_string(
            ship_date
            or (picking.scheduled_date.date() if picking.scheduled_date else None)
            or fields.Date.context_today(self.carrier_id)
        )
        pkg_count = max(
            1,
            len(picking.move_line_ids.mapped("result_package_id"))
            or getattr(picking, "number_of_packages", 0)
            or 1,
        )
        carrier = self.carrier_id
        if is_return:
            consignor_block = self._prepare_partner_data(
                partner, include_id=False, is_consignor=False
            )
            consignee_block = self._prepare_partner_data(
                shipper_partner, include_id=True, is_consignor=True, minimal=False
            )
            refs = [{"code": "100", "value": f"RET-{picking.name}"[:35]}]
        else:
            consignor_block = self._prepare_partner_data(
                shipper_partner, include_id=True, is_consignor=True, minimal=False
            )
            consignee_block = self._prepare_partner_data(
                partner, include_id=False, is_consignor=False
            )
            refs = self._prepare_references(picking)

        shipment = {
            "division": self.division,
            "product": self.product,
            "shipmentDate": eff_date,
            "forwarder": {"id": (carrier.dachser_forwarder_id or "193").strip()},
            "consignor": consignor_block,
            "consignee": consignee_block,
            "references": refs,
        }
        if existing_ssccs:
            shipment["ssccs"] = existing_ssccs

        return {
            "format": (carrier.dachser_label_format or "P").upper(),
            "count": min(10, pkg_count),
            "fontFileName": (carrier.dachser_font_file_name or "ARIALR.FNT").strip(),
            "labelTypes": self._get_label_types_list(),
            "shipment": shipment,
        }

    # -------------------------------------------------------------------------
    # High-Level REST API v2 Operations
    # -------------------------------------------------------------------------
    def rate_shipment(self, order):
        """Query `POST /rest/v2/quotations` for a `sale.order`."""
        partner = order.partner_shipping_id or order.partner_id
        if not partner.country_id or not partner.zip:
            return {
                "success": False,
                "price": 0.0,
                "currency": "EUR",
                "error_message": _(
                    "The consignee (%s) must have a Postal Code and Country "
                    "to calculate the Dachser rate."
                )
                % partner.display_name,
            }
        res = self._request(
            "POST",
            "quotations",
            json_payload=self._prepare_quotation_data(order),
            raise_on_error=False,
        )
        if res.get("_error"):
            return {
                "success": False,
                "price": 0.0,
                "currency": "EUR",
                "error_message": res.get("error_message"),
            }
        total_block = res.get("totalAmount") or {}
        amount = float(total_block.get("amount") or 0.0)
        currency_code = total_block.get("currency") or "EUR"
        if amount <= 0.0:
            return {
                "success": False,
                "price": 0.0,
                "currency": currency_code,
                "error_message": _(
                    "Dachser Quotation API did not return an immediate price "
                    "for this shipment."
                ),
            }
        return {
            "success": True,
            "price": amount,
            "currency": currency_code,
            "error_message": False,
        }

    def send_shipping(self, picking):
        """Submit picking via `POST /rest/v2/transportorders/{basket}` or
        `POST /rest/v2/labels` (with automatic test-mode fallback on 401/403).
        """
        mode = self.carrier_id.dachser_operation_mode or "transportorder"
        basket = self.carrier_id.dachser_basket or "sent"
        order_id = False
        order_state = basket
        ssccs = []
        label_b64 = False
        ldr_routing = False

        if mode == "transportorder":
            to_payload = self._prepare_shipment_data(picking)
            resp = self._request(
                "POST",
                f"transportorders/{basket}",
                json_payload=to_payload,
                raise_on_error=bool(self.carrier_id.prod_environment),
            )
            if isinstance(resp, dict) and resp.get("_error"):
                if resp.get("status_code") in (401, 403):
                    _logger.info(
                        "Dachser test token fallback to /rest/v2/labels for %s",
                        picking.name,
                    )
                    mode = "label_only"
                else:
                    raise UserError(
                        _("Dachser API Error:\n%s") % resp.get("error_message", "")
                    )
            else:
                order_id = str(resp.get("id") or "")
                order_state = resp.get("state") or basket
                ssccs = resp.get("ssccs") or []
                label_b64 = resp.get("label") or False

        if mode == "label_only":
            lbl_resp = self._request(
                "POST",
                "labels",
                json_payload=self._prepare_label_data(picking),
            )
            order_state = "labelled"
            ssccs = lbl_resp.get("ssccs") or []
            label_b64 = lbl_resp.get("label") or False
            relation = lbl_resp.get("relation") or {}
            ldr_routing = (
                relation.get("printableRelation")
                or relation.get("relationCode")
                or False
            )

        tracking_refs = ", ".join(ssccs) if ssccs else (order_id or picking.name)
        return {
            "tracking_number": tracking_refs,
            "order_id": order_id,
            "state": order_state,
            "ssccs": ssccs,
            "label": label_b64,
            "ldr_routing": ldr_routing,
        }

    def send_transport_order(self, order_id):
        """Transmit an `imported` or `labelled` order
        (`POST /transportorders/{id}/send`).
        """
        carrier = self.carrier_id
        label_format = carrier.dachser_label_format or "P"
        params = {
            "label-format": label_format,
            "label-types": ",".join(self._get_label_types_list()),
        }
        if label_format == "Z" and carrier.dachser_font_file_name:
            params["font-file-name"] = carrier.dachser_font_file_name.strip()
        return self._request(
            "POST",
            f"transportorders/{int(order_id)}/send",
            params=params,
        )

    def get_label(self, picking):
        """Download or reprint label via `/transportorders/{id}/labels` or `/labels`."""
        carrier = self.carrier_id
        meta = picking.tracking_json if isinstance(picking.tracking_json, dict) else {}
        order_id = meta.get("transport_order_id")
        if order_id:
            label_format = carrier.dachser_label_format or "P"
            params = {
                "label-format": label_format,
                "label-types": ",".join(self._get_label_types_list()),
            }
            if label_format == "Z" and carrier.dachser_font_file_name:
                params["font-file-name"] = carrier.dachser_font_file_name.strip()
            return self._request(
                "POST",
                f"transportorders/{int(order_id)}/labels",
                params=params,
            )
        existing_ssccs = meta.get("ssccs") or [
            s.strip()
            for s in (picking.carrier_tracking_ref or "").split(",")
            if s.strip()
        ]
        return self._request(
            "POST",
            "labels",
            json_payload=self._prepare_label_data(
                picking, existing_ssccs=existing_ssccs
            ),
        )

    def get_return_label(self, picking, origin_date=None):
        """Generate return label via `POST /rest/v2/labels`."""
        return self._request(
            "POST",
            "labels",
            json_payload=self._prepare_label_data(
                picking, is_return=True, ship_date=origin_date
            ),
        )

    def cancel_shipping(self, order_ref):
        """Cancel transport order (`DELETE /rest/v2/transportorders/{id}`)."""
        resp = self._request(
            "DELETE",
            f"transportorders/{order_ref}",
            raise_on_error=False,
        )
        return not (isinstance(resp, dict) and resp.get("_error"))

    @staticmethod
    def _normalize_shipment_items(raw_data):
        if isinstance(raw_data, dict) and "shipments" in raw_data:
            return raw_data.get("shipments", [])
        if isinstance(raw_data, list):
            return raw_data
        return []

    @staticmethod
    def _extract_latest_event(status_block):
        if isinstance(status_block, list):
            latest_event = status_block[-1] if status_block else {}
            for st in status_block:
                if isinstance(st, dict) and st.get("statusSequence") == 1:
                    latest_event = st
                    break
        elif isinstance(status_block, dict):
            latest_event = status_block
        else:
            latest_event = {}

        event_obj = (
            latest_event.get("event")
            if isinstance(latest_event.get("event"), dict)
            else latest_event
        )
        event_code = str(event_obj.get("code") or "")
        event_desc = event_obj.get("description") or ""
        event_date = (
            latest_event.get("date")
            or latest_event.get("statusDate")
            or event_obj.get("date")
            or ""
        )
        event_loc = latest_event.get("location") or event_obj.get("location") or ""
        reason_desc = (
            latest_event.get("reasonDescription")
            or event_obj.get("reasonDescription")
            or ""
        )
        return (
            latest_event,
            event_code,
            event_desc,
            event_date,
            event_loc,
            reason_desc,
        )

    @staticmethod
    def _format_tracking_history(history_items, status_block, latest_event):
        lines = []
        hist_source = (
            history_items[-1].get("status", [])
            if history_items
            else (status_block if isinstance(status_block, list) else [])
        )
        if isinstance(hist_source, dict):
            hist_source = [hist_source]
        elif not hist_source and latest_event:
            hist_source = [latest_event]

        if (
            len(hist_source) > 1
            and isinstance(hist_source[0], dict)
            and "statusSequence" in hist_source[0]
        ):
            hist_source = list(reversed(hist_source))

        for ev in hist_source:
            ev_inner = ev.get("event") if isinstance(ev.get("event"), dict) else ev
            ev_dt = ev.get("date") or ev.get("statusDate") or ev_inner.get("date") or ""
            ev_code = ev_inner.get("code") or ""
            ev_desc = ev_inner.get("description") or ""
            ev_loc = ev.get("location") or ev_inner.get("location") or ""
            line = f"- {ev_dt}: [{ev_code}] {ev_desc}"
            if ev_loc:
                line += f" ({ev_loc})"
            lines.append(line)
        return lines

    def get_pod(self, tracking_number, raise_on_error=True):
        """Query `GET /rest/v2/pods` for signed Proof of Delivery."""
        params = {"tracking-number": str(tracking_number).strip()}
        if self.carrier_id.dachser_consignor_id:
            params["customer-id"] = self.carrier_id.dachser_consignor_id.strip()
        return self._request(
            "GET",
            "pods",
            params=params,
            raise_on_error=raise_on_error,
        )

    def get_tracking(self, picking):
        """Query `/shipmentstatus`, `/shipmenthistory`, and (when delivered) `/pods`."""
        meta = (
            dict(picking.tracking_json)
            if isinstance(picking.tracking_json, dict)
            else {}
        )
        tracking_ref = (
            meta.get("consignment_id")
            or str(picking.carrier_tracking_ref or "").split(",")[0].strip()
        )
        params = {"tracking-number": tracking_ref}
        if self.carrier_id.dachser_consignor_id:
            params["customer-id"] = self.carrier_id.dachser_consignor_id.strip()

        status_raw = self._request("GET", "shipmentstatus", params=params)
        history_raw = self._request(
            "GET", "shipmenthistory", params=params, raise_on_error=False
        )
        if isinstance(history_raw, dict) and history_raw.get("_error"):
            history_raw = []

        status_items = self._normalize_shipment_items(status_raw)
        history_items = self._normalize_shipment_items(history_raw)
        if not status_items and not history_items:
            return {
                "delivery_state": False,
                "tracking_state": False,
                "tracking_state_history": False,
                "tracking_json": meta,
                "pod": False,
                "pod_filename": False,
            }

        info = (status_items[-1] if status_items else history_items[-1]) or {}
        consignment_id = info.get("consignmentId") or meta.get("consignment_id")
        pod_signor = info.get("podSignor")
        status_block = info.get("status")
        (
            latest_event,
            event_code,
            event_desc,
            _event_date,
            event_loc,
            reason_desc,
        ) = self._extract_latest_event(status_block)
        history_lines = self._format_tracking_history(
            history_items, status_block, latest_event
        )
        delivery_state = map_dachser_status_to_delivery_state(event_code, event_desc)

        tracking_state = event_desc
        if event_loc:
            tracking_state = f"{tracking_state} ({event_loc})"
        if reason_desc:
            tracking_state = f"{tracking_state} - {reason_desc}"
        if pod_signor:
            tracking_state = f"{tracking_state} [{pod_signor}]"

        if consignment_id:
            meta["consignment_id"] = consignment_id
        if pod_signor:
            meta["pod_signor"] = pod_signor
        meta["events"] = history_raw or status_raw

        pod_b64 = False
        pod_filename = False
        if delivery_state == "customer_delivered" and not picking.pod_file:
            pods = self.get_pod(consignment_id or tracking_ref, raise_on_error=False)
            if isinstance(pods, list) and pods and pods[0].get("podDocument"):
                pod_b64 = pods[0]["podDocument"]
                cid = pods[0].get("consignmentId") or consignment_id or tracking_ref
                pod_filename = f"dachser_pod_{cid}.pdf"

        return {
            "delivery_state": delivery_state,
            "tracking_state": tracking_state,
            "tracking_state_history": "\n".join(history_lines)
            if history_lines
            else tracking_state,
            "tracking_json": meta,
            "pod": pod_b64,
            "pod_filename": pod_filename,
        }

    def get_routing(self, partner, shipment_date=None):
        """Query `GET /rest/v2/routings` for LDR routing validation."""
        params = {
            "branch-id": (self.carrier_id.dachser_forwarder_id or "193").strip(),
            "division": self.division,
            "product": self.product,
            "country-code": (partner.country_id.code or "ES").upper(),
            "postal-code": (partner.zip or "00000").strip(),
        }
        if shipment_date:
            params["shipment-date"] = str(shipment_date).strip()
        if partner.city:
            params["city"] = partner.city.strip()
        return self._request("GET", "routings", params=params)

    def get_ssccs(self, count=1, use_prefix=True):
        """Query `POST /rest/v2/ssccs` to allocate SSCC barcodes."""
        payload = {
            "count": min(max(int(count), 1), 100),
            "usePrefix": bool(use_prefix),
        }
        return self._request("POST", "ssccs", json_payload=payload)

    def get_transfer_list(self, order_date, order_group=None, lang=None):
        """Query `GET /rest/v2/transferlists/{orderdate}` for daily manifest PDF."""
        params = {}
        if order_group:
            params["order-group"] = str(order_group).strip()
        return self._request(
            "GET",
            f"transferlists/{order_date}",
            params=params or None,
            lang=lang,
        )
