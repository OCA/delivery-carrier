# -*- coding: utf-8 -*-
# Copyright 2021 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from collections import defaultdict

from odoo import _, models
from odoo.exceptions import ValidationError


GLS_MAX_LENGTHS = defaultdict(lambda: 40)
GLS_MAX_LENGTHS.update(eMail=80, ZIPCode=10, CountryCode=2)


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
        return address_payload
