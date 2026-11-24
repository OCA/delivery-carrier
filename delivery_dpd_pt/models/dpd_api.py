# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

"""DPD Portugal API helpers (shipment specification)."""

import base64
import binascii
import re
from urllib.parse import urlencode

import phonenumbers

from odoo.exceptions import UserError

URLS = {
    "test": "https://qabusiness.dpd.pt/api/v1/pt",
    "prod": "https://business.dpd.pt/api/v1/pt",
}
METHODS = {
    "create": ("POST", "expedition/registarExpedicao"),
    "label": ("GET", "expedition/etiquetaApi/"),
    "zpl": ("POST", "expedition/zplApi/"),
    "lookup": ("GET", "expedition/guia/"),
    "cancel": ("POST", "expedition/cancelar"),
}


def text(env, value, label, limit, required=True):
    value = " ".join(str(value or "").split())
    if required and not value:
        raise UserError(env._("Please fill in %s.", label))
    if len(value) > limit:
        raise UserError(
            env._(
                "%(label)s: maximum of %(limit)s characters (currently %(length)s).",
                label=label,
                limit=limit,
                length=len(value),
            )
        )
    return value


def phone(env, value, country):
    try:
        number = phonenumbers.parse(value or "", country or "PT")
        national = phonenumbers.national_significant_number(number)
        if not phonenumbers.is_valid_number(number) or len(national) > 15:
            raise ValueError()
        return national, "+" + str(number.country_code)
    except (phonenumbers.NumberParseException, ValueError):
        raise UserError(
            env._(
                "Enter a valid contact phone number with international "
                "dialing code. The DPD API accepts up to 15 digits in the "
                "national number."
            )
        ) from None


def postcode(env, value, country, required=True):
    value = text(env, value, env._("Postcode"), 8, required=required)
    if country == "PT" and value:
        digits = re.sub(r"[- ]", "", value)
        if not re.fullmatch(r"\d{7}", digits):
            raise UserError(
                env._("The Portuguese postcode must use the 0000-000 format.")
            )
        value = digits[:4] + "-" + digits[4:]
    return value


def guide_numbers(env, value):
    if isinstance(value, (str, int)):
        value = [value]
    if not isinstance(value, list) or not value:
        raise UserError(
            env._(
                "DPD did not return a recognizable guide number. Check the "
                "DPD portal before repeating the shipment."
            )
        )
    if any(isinstance(v, bool) or not isinstance(v, (str, int)) for v in value):
        raise UserError(
            env._(
                "The guide numbers returned by DPD are invalid. Check the DPD portal."
            )
        )
    numbers = [str(v).strip() for v in value]
    if any(not v for v in numbers) or len(set(numbers)) != len(numbers):
        raise UserError(
            env._(
                "The guide numbers returned by DPD are invalid. Check the DPD portal."
            )
        )
    return numbers


def pdf_bytes(value):
    if not isinstance(value, str) or not value or len(value) > 28_000_000:
        raise ValueError("Missing or oversized label")
    raw = base64.b64decode("".join(value.split()), validate=True)
    if not raw.startswith(b"%PDF-"):
        raise ValueError("Invalid PDF")
    return raw


def zpl_bytes(value):
    if not isinstance(value, str) or not value:
        raise ValueError("Missing label")
    compact = "".join(value.split())
    try:
        raw = base64.b64decode(compact, validate=True)
    except (binascii.Error, ValueError):
        raw = value.encode()
    if not raw.strip():
        raise ValueError("Invalid ZPL")
    return raw


def tracking_url(reference):
    return "https://tracking.dpd.pt/pt/getting-parcel/track-trace?" + urlencode(
        {"reference": reference}
    )
