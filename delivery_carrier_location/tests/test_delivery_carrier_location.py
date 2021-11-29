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
        # Cities
        cls.paris = cls.env["res.city"].create(
            {
                "name": "Paris",
                "state_id": cls.ile_de_france.id,
                "country_id": cls.france.id,
                "zipcode": "75000",
            }
        )
        # Locations
        cls.paris_01 = cls.env["res.city.zip"].create(
            {"name": "75001", "city_id": cls.paris.id}
        )
        cls.paris_02 = cls.env["res.city.zip"].create(
            {"name": "75002", "city_id": cls.paris.id}
        )
        cls.paris_03 = cls.env["res.city.zip"].create(
            {"name": "75003", "city_id": cls.paris.id}
        )
        cls.paris_04 = cls.env["res.city.zip"].create(
            {"name": "75004", "city_id": cls.paris.id}
        )
        cls.paris_05 = cls.env["res.city.zip"].create(
            {"name": "75005", "city_id": cls.paris.id}
        )
        cls.paris_06 = cls.env["res.city.zip"].create(
            {"name": "75006", "city_id": cls.paris.id}
        )
        cls.paris_07 = cls.env["res.city.zip"].create(
            {"name": "75007", "city_id": cls.paris.id}
        )
        cls.paris_08 = cls.env["res.city.zip"].create(
            {"name": "75008", "city_id": cls.paris.id}
        )
        cls.paris_09 = cls.env["res.city.zip"].create(
            {"name": "75009", "city_id": cls.paris.id}
        )
        cls.paris_10 = cls.env["res.city.zip"].create(
            {"name": "75010", "city_id": cls.paris.id}
        )
        cls.paris_11 = cls.env["res.city.zip"].create(
            {"name": "75011", "city_id": cls.paris.id}
        )
        # Disable all other delivery methods
        cls.env["delivery.carrier"].search([]).write({"active": False})
        # Create delivery methods
        cls.product = cls.env["product.product"].create({"name": "Delivery"})
        cls.carrier_paris_01_05 = cls.env["delivery.carrier"].create(
            {
                "name": "Delivery in Paris 01-05",
                "product_id": cls.product.id,
                "delivery_type": "fixed",
                "fixed_price": 20,
                "sequence": 10,
                "country_ids": [(4, cls.france.id)],
                "zip_ids": [
                    (4, cls.paris_01.id),
                    (4, cls.paris_02.id),
                    (4, cls.paris_03.id),
                    (4, cls.paris_04.id),
                    (4, cls.paris_05.id),
                ],
            }
        )
        cls.carrier_paris_06_11 = cls.env["delivery.carrier"].create(
            {
                "name": "Delivery in Paris 06-11",
                "product_id": cls.product.id,
                "delivery_type": "fixed",
                "fixed_price": 15,
                "sequence": 10,
                "country_ids": [(4, cls.france.id)],
                "zip_ids": [
                    (4, cls.paris_06.id),
                    (4, cls.paris_07.id),
                    (4, cls.paris_08.id),
                    (4, cls.paris_09.id),
                    (4, cls.paris_10.id),
                    (4, cls.paris_11.id),
                ],
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

    def test_00_partner_zip_id(self):
        # Partner living in paris 03, with zip_id set
        partner = self.env["res.partner"].create(
            {
                "name": "Edgar Degas",
                "city_id": self.paris.id,
                "state_id": self.paris.state_id.id,
                "country_id": self.paris.country_id.id,
                "zip_id": self.paris_03.id,
                "zip": self.paris_03.name,
            }
        )
        # Check available carriers
        carriers = self._get_available_carriers(partner)
        self.assertIn(self.carrier_paris_01_05, carriers)
        self.assertNotIn(self.carrier_paris_06_11, carriers)

    def test_01_partner_zip_but_without_zip_id(self):
        # Partner living in paris 08, but zip_id is not set
        partner = self.env["res.partner"].create(
            {
                "name": "Claude Monet",
                "city_id": self.paris.id,
                "state_id": self.paris.state_id.id,
                "country_id": self.paris.country_id.id,
                "zip_id": False,
                "zip": self.paris_08.name,
            }
        )
        # Check available carriers
        carriers = self._get_available_carriers(partner)
        self.assertIn(self.carrier_paris_06_11, carriers)
        self.assertNotIn(self.carrier_paris_01_05, carriers)
