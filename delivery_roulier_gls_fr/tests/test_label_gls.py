# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.addons.base_delivery_carrier_label.tests import carrier_label_case
from vcr_unittest import VCRMixin


class GlsLabelCase(VCRMixin, carrier_label_case.CarrierLabelCase):
    def setUp(self, *args, **kwargs):
        super().setUp(*args, **kwargs)
        # french carrier sender need to be from France
        self.picking.company_id.partner_id.write(
            {"country_id": self.env.ref("base.fr").id}
        )

    def _get_vcr_kwargs(self, **kwargs):
        return {
            "record_mode": "once",
            "match_on": ["method", "path"],
            "decode_compressed_response": True,
        }

    def _product_data(self):
        data = super()._product_data()
        data.update({"weight": 1.2})
        return data

    def _create_order_picking(self):
        super()._create_order_picking()

    def _get_carrier(self):
        return self.env.ref("delivery_roulier_gls_fr.delivery_carrier_gls")

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
