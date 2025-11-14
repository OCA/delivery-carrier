# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from vcr_unittest import VCRMixin

from odoo.addons.base_delivery_carrier_label.tests import carrier_label_case


class GeodisFrLabelCase(VCRMixin, carrier_label_case.TestCarrierLabel):
    def setUp(self, *args, **kwargs):
        # need it to be defined before super to avoid failure in _hide_sensitive_data
        self.account = False
        super().setUp(*args, **kwargs)
        # french carrier sender need to be from France
        self.picking.company_id.partner_id.write(
            {
                "country_id": self.env.ref("base.fr").id,
                "city": "VILLEURBANNE",
                "zip": "69100",
            }
        )
        self.account = self.env["carrier.account"].create(
            {
                "name": "Geodis - France Express",
                "delivery_type": "geodis_fr",
                # fill real account information if you want to re-generate cassette
                "account": "45393e38323033372b3c3334",
                "password": "2d5a44584356",
                "geodis_fr_customer_id": "787000",
            }
        )
        carrier = self.env.ref("delivery_roulier_geodis_fr.delivery_carrier_mes")
        carrier.carrier_account_id = self.account.id
        self.agency = self.env["delivery.carrier.agency"].create(
            {
                "name": "Lille Agency",
                "external_reference": "459059",
                "delivery_type": "geodis_fr",
                "partner_id": self.env.ref(
                    "delivery_roulier_geodis_fr.default_geodis_france_exress_agency_partner"
                ).id,
                "geodis_fr_interchange_sender": "222222222",
                "geodis_fr_interchange_recipient": "111111111",
                "geodis_fr_hub_id": "159",
            }
        )

    def _hide_sensitive_data(self, request):
        password = self.account and self.account.password or "dummy"
        account = self.account and self.account.account or "dummy"
        customer_id = self.account and self.account.geodis_fr_customer_id or "dummy"
        body = request.body
        body = body.replace(password.encode(), b"password")
        body = body.replace(account.encode(), b"000000")
        body = body.replace(customer_id.encode(), b"000000")
        request.body = body
        return request

    def _get_vcr_kwargs(self, **kwargs):
        return {
            "record_mode": "once",
            "match_on": ["method", "path"],
            "decode_compressed_response": True,
            "before_record_request": self._hide_sensitive_data,
        }

    def _transfer_order_picking(self):
        for move in self.picking.move_ids:
            move.quantity_done = move.product_uom_qty
        move_lines = self.picking.move_line_ids
        self.picking._put_in_pack(move_lines)
        return super()._transfer_order_picking()

    def _product_data(self):
        data = super()._product_data()
        data.update(
            {
                "weight": 1.2,
            }
        )
        return data

    def _create_order_picking(self):
        return super()._create_order_picking()

    def _get_carrier(self):
        return self.env.ref("delivery_roulier_geodis_fr.delivery_carrier_mes")

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

    def test_labels_and_edi(self):
        res = super().test_labels()
        self.assertTrue(self.picking.geodis_shippingid)
        deposit = self.env["deposit.slip"].create(
            {
                "name": "test",
                "delivery_type": "geodis_fr",
                "picking_ids": [(6, 0, self.picking.ids)],
            }
        )
        deposit.validate_deposit()
        attachment = self.env["ir.attachment"].search(
            [("res_id", "=", deposit.id), ("res_model", "=", "deposit.slip")]
        )
        self.assertEqual(len(attachment), 1)
        self.assertTrue(attachment.datas)
        return res

    def test_addresses(self):
        addresses = self.picking._geodis_fr_get_address_proposition()
        self.assertEqual(len(addresses), 1)
        self.picking.partner_id.write({"zip": 69155, "city": "VILLURB"})
        addresses = self.picking._geodis_fr_get_address_proposition(raise_address=False)
        self.assertEqual(len(addresses), 0)
