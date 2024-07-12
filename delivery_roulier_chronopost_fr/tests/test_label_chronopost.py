# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import pytest

from odoo.addons.base_delivery_carrier_label.tests import carrier_label_case


class ChronopostLabelCase(carrier_label_case.TestCarrierLabel):
    @classmethod
    def setUpClass(cls):
        # need it to be defined before super to avoid failure in _hide_sensitive_data
        cls.account = False
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        # french carrier sender need to be from France
        cls.picking.company_id.partner_id.write(
            {"country_id": cls.env.ref("base.fr").id}
        )
        # change account and password with valid credentials to regenerate the cassette
        cls.account = cls.env["carrier.account"].create(
            {
                "name": "Chronopost Test Account",
                "delivery_type": "chronopost_fr",
                "account": "dummy",
                "password": "dummy",
                "chronopost_fr_file_format": "Z2D",
            }
        )

    @classmethod
    def _hide_sensitive_data(self, request):
        password = self.account and self.account.password or "dummy"
        account = self.account and self.account.account or "dummy"
        body = request.body
        body = body.replace(password.encode(), b"password")
        body = body.replace(account.encode(), b"00000000")
        request.body = body
        return request

    @classmethod
    @pytest.fixture(scope="module")
    def vcr_config(self):
        return {
            "filter_headers": ["authorization"],
            "ignore_localhost": True,
            "record_mode": "once",
            "match_on": ["method", "path"],
            "decode_compressed_response": True,
            "before_record_request": self._hide_sensitive_data,
        }

    def _product_data(self):
        data = super()._product_data()
        data.update({"weight": 1.2})
        return data

    def _get_carrier(self):
        return self.env.ref("delivery_roulier_chronopost_fr.chrono_13")

    def _partner_data(self):
        data = super()._partner_data()
        data.update(
            {
                "street": "27 Rue Henri Rolland",
                "zip": "69100",
                "city": "VILLEURBANNE",
                "country_id": self.env.ref("base.fr").id,
            }
        )
        return data
