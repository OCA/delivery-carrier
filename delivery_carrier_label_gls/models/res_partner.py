# -*- coding: utf-8 -*-
# Copyright 2021 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from collections import defaultdict
import re

from odoo import _, models
from odoo.exceptions import ValidationError


GLS_MAX_LENGTHS = defaultdict(lambda: 40)
GLS_MAX_LENGTHS.update(eMail=80, ZIPCode=10, CountryCode=2)


def keep_alphanumeric(s):
    return re.sub("[\W_]", "", s)


def keep_digits(s):
    return re.sub("[^0-9]", "", s)


def len_is(n):
    return lambda s: len(s) == n


country_normalize_validate = {
    "BE": (keep_digits, len_is(4)),
    "LU": (keep_digits, len_is(4)),
    "FR": (keep_digits, len_is(5)),
    "DE": (keep_digits, len_is(5)),
}
COUNTRY_NORMALIZE_VALIDATE = defaultdict(lambda: (keep_alphanumeric, lambda s: bool(s)))
COUNTRY_NORMALIZE_VALIDATE.update(country_normalize_validate)


class ResPartner(models.Model):
    _inherit = "res.partner"

    def _gls_prepare_address(self):
        self.ensure_one()
        address_payload = {}
        mapping = {
            "name": "Name1",
            "street": "Street",
            "street2": "StreetNumber",
            "city": "City",
            "email": "eMail",
            "zip": "ZIPCode",
            "phone": "FixedLinePhonenumber",
            "mobile": "MobilePhoneNumber",
            "country_id.code": "CountryCode",
            "state_id.name": "Province",
        }
        mapping_optional = {"phone", "mobile", "street2", "state_id.name"}
        for key in mapping:
            if "." in key:
                value = self.mapped(key)
                value = value[0] if value else value
            else:
                value = self[key]
            if not value and key not in mapping_optional:
                msg = _("Missing required parameter %s on partner %s")
                raise ValidationError(msg % (key, self.name))
            if value:
                gls_key = mapping[key]
                address_payload[gls_key] = value[:GLS_MAX_LENGTHS[gls_key]]
        address_payload["ZIPCode"] = self._get_iso_zip(validate_raises=True)
        return address_payload

    def _get_iso_zip(self, validate_raises=False):
        """GLS does not support common ways to format the zip, and will raise.
           Typically in Luxembourg they are written L-4280 or in certain countries
           they might add some space or dash for readability.
        """
        self.ensure_one()
        normalize, validate = COUNTRY_NORMALIZE_VALIDATE[self.country_id.code]
        iso_zip = normalize(self.zip)
        if validate_raises and not validate(iso_zip):
            msg = _("Not a valid ZIP code for country %s: %s")
            raise ValidationError(msg % (self.country_id.code, self.zip))
        return iso_zip
