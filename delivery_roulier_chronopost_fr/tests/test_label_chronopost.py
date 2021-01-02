# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from vcr_unittest import VCRMixin

from odoo.addons.base_delivery_carrier_label.tests import carrier_label_case


class ChronopostLabelCase(VCRMixin, carrier_label_case.CarrierLabelCase):
    def setUp(self, *args, **kwargs):
        # need it to be defined before super to avoid failure in _hide_sensitive_data
        self.account = False
        super().setUp(*args, **kwargs)
        # french carrier sender need to be from France
        self.picking.company_id.partner_id.write(
            {"country_id": self.env.ref("base.fr").id}
        )
        # change account and password with valid credentials to regenerate the cassette
        self.account = self.env["carrier.account"].create(
            {
                "name": "Chronopost Test Account",
                "delivery_type": "chronopost_fr",
                "account": "dummy",
                "password": "dummy",
                "chronopost_fr_file_format": "Z2D",
            }
        )

    def _hide_sensitive_data(self, request):
        password = self.account and self.account.password or "dummy"
        account = self.account and self.account.account or "dummy"
        body = request.body
        body = body.replace(password.encode(), b"password")
        body = body.replace(account.encode(), b"00000000")
        request.body = body
        return request

    def _get_vcr_kwargs(self, **kwargs):
        return {
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
