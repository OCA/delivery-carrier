# Copyright 2021 Camptocamp
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import SavepointCase


class TestPackageFee(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))

        # Companies
        cls.company0 = cls.env["res.company"].create({"name": "Avengers"})
        cls.company1 = cls.env["res.company"].create({"name": "S.H.I.E.L.D."})
        cls.company2 = cls.env["res.company"].create({"name": "X-Men"})

        # Carriers (the first one is just an empty recordset -> no carrier!)
        cls.carrier0 = cls.env["delivery.carrier"]
        cls.carrier1 = cls.env["delivery.carrier"].create(
            {
                "name": "Helicarrier",
                "fixed_price": 1.0,
                "product_id": cls.env["product.product"]
                .create({"name": "Shipping1", "type": "service"})
                .id,
            }
        )
        cls.carrier2 = cls.env["delivery.carrier"].create(
            {
                "name": "Blackbird",
                "fixed_price": 1.0,
                "product_id": cls.env["product.product"]
                .create({"name": "Shipping1", "type": "service"})
                .id,
            }
        )

        # Add everything into proper attributes
        cls.carriers = [cls.carrier0, cls.carrier1, cls.carrier2]
        cls.companies = [cls.company0, cls.company1, cls.company2]
        cls.couples = tuple(zip(cls.companies, cls.carriers))

        # Allow user to use only the new companies
        # You need to do this in this exact order, otherwise an error will
        # be raised
        cls.env.user.company_ids |= cls.company0
        cls.env.user.company_id = cls.company0
        cls.env.user.company_ids = cls.env["res.company"].union(*cls.companies)

    def _config_create(self, carrier):
        return self.env["res.config.settings"].create(
            {"partner_default_delivery_carrier_id": int(carrier)}
        )

    def _partner_create(self):
        return self.env["res.partner"].create({"name": "MockupPartner"})

    def test_00_partner_create(self):
        for company, carrier in self.couples:
            # Switch user company
            self.env.user.company_id = company
            # Create config with current carrier, save it
            config = self._config_create(carrier.id)
            config.execute()
            # Create new partner, get its carrier
            pcarrier = self._partner_create().property_delivery_carrier_id
            # Check if partner's carrier is the current carrier
            self.assertEqual(pcarrier.id, carrier.id)

        # Check that 3 `ir.default` records were created
        mname, fname = "res.partner", "property_delivery_carrier_id"
        field = self.env["ir.model.fields"]._get(mname, fname)
        domain = [("field_id", "=", field.id)]
        count = self.env["ir.default"].sudo().search_count(domain)
        self.assertEqual(count, 3)
