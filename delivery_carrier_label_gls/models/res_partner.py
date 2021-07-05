# -*- coding: utf-8 -*-
# Copyright 2021 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, models
from odoo.exceptions import ValidationError


class ResPartner(models.Model):
    _inherit = "res.partner"

    def _gls_prepare_address(self):
        self.ensure_one()
        address_payload = {}
        mapping = {
            "name": "Name1",
            "street": "Street",
            "city": "City",
            "email": "eMail",
            "zip": "ZIPCode",
            "phone": "FixedLinePhonenumber",
            "mobile": "MobilePhoneNumber",
            "country_id.code": "CountryCode",
            "state_id.name": "Province",
        }
        mapping_optional = {"phone", "mobile", "state_id.name"}
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
                address_payload[mapping[key]] = value
        return address_payload
