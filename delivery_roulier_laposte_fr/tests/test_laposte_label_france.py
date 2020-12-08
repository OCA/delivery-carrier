# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from vcr_unittest import VCRMixin

from odoo.addons.base_delivery_carrier_label.tests import carrier_label_case


class LaposteLabelFranceCase(VCRMixin, carrier_label_case.CarrierLabelCase):
    def setUp(self, *args, **kwargs):
        # need it to be defined before super to avoid failure in _hide_sensitive_data
        self.account = False
        super().setUp(*args, **kwargs)
        # french carrier sender need to be from France
        self.picking.company_id.partner_id.write(
            {"country_id": self.env.ref("base.fr").id}
        )
        self.account = self.env["carrier.account"].create(
            {
                "name": "Laposte",
                "delivery_type": "laposte_fr",
                # fill real account information if you want to re-generate cassette
                "account": "dummy",
                "password": "dummy",
            }
        )

    def _hide_sensitive_data(self, request):
        password = self.account and self.account.password or "dummy"
        account = self.account and self.account.account or "dummy"
        body = request.body
        body = body.replace(password.encode(), b"password")
        body = body.replace(account.encode(), b"000000")
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

    def _create_order_picking(self):
        super()._create_order_picking()

    def _get_carrier(self):
        return self.env.ref("delivery_roulier_laposte_fr.delivery_carrier_DOM")

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
