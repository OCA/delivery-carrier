# Copyright 2021 Camptocamp SA - Iván Todorovich
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests import common


class TestDeliveryCarrierCity(common.SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        # Countries
        cls.france = cls.env.ref("base.fr")
        # States
        cls.ile_de_france = cls.env["res.country.state"].create(
            {
                "name": "Île-de-France",
                "code": "FR-IDF",
                "country_id": cls.france.id,
            }
        )
        cls.cote_azur = cls.env["res.country.state"].create(
            {
                "name": "Provence-Alpes-Côte-d'Azur",
                "code": "FR-PAC",
                "country_id": cls.france.id,
            }
        )
        # Cities
        cls.paris = cls.env["res.city"].create(
            {
                "name": "Paris",
                "state_id": cls.ile_de_france.id,
                "country_id": cls.france.id,
                "zipcode": "75000",
            }
        )
        cls.nice = cls.env["res.city"].create(
            {
                "name": "Nice",
                "state_id": cls.cote_azur.id,
                "country_id": cls.france.id,
                "zipcode": "06000",
            }
        )
        # Disable all other delivery methods
        cls.env["delivery.carrier"].search([]).write({"active": False})
        # Create delivery methods
        cls.product = cls.env["product.product"].create({"name": "Delivery"})
        cls.carrier_paris = cls.env["delivery.carrier"].create(
            {
                "name": "Delivery in Paris",
                "product_id": cls.product.id,
                "delivery_type": "fixed",
                "fixed_price": 15,
                "sequence": 10,
                "country_ids": [(4, cls.france.id)],
                "city_ids": [(4, cls.paris.id)],
            }
        )
        cls.carrier_france = cls.env["delivery.carrier"].create(
            {
                "name": "Delivery in France",
                "product_id": cls.product.id,
                "delivery_type": "fixed",
                "fixed_price": 25,
                "sequence": 20,
                "country_ids": [(4, cls.france.id)],
            }
        )

    def _get_available_carriers(self, partner):
        return self.env["delivery.carrier"].search([]).available_carriers(partner)

    def test_00_delivery_carrier_city_match(self):
        # Partner living in paris
        partner = self.env["res.partner"].create(
            {
                "name": "Edgar Degas",
                "city_id": self.paris.id,
                "state_id": self.paris.state_id.id,
                "country_id": self.paris.country_id.id,
            }
        )
        # Check available carriers
        carriers = self._get_available_carriers(partner)
        self.assertIn(self.carrier_france, carriers)
        self.assertIn(self.carrier_paris, carriers)

    def test_01_delivery_carrier_city_not_match(self):
        # Partner not living in paris
        partner = self.env["res.partner"].create(
            {
                "name": "Henri Matisse",
                "city_id": self.nice.id,
                "state_id": self.nice.state_id.id,
                "country_id": self.nice.country_id.id,
            }
        )
        # Check available carriers
        carriers = self._get_available_carriers(partner)
        self.assertIn(self.carrier_france, carriers)
        self.assertNotIn(self.carrier_paris, carriers)
