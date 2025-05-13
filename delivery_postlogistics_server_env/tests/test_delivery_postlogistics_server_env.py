# Copyright 2021 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests import TransactionCase


class TestDeliveryCarrier(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Create a delivery product
        cls.delivery_product = cls.env["product.product"].create(
            {
                "name": "Test Delivery Product",
                "type": "service",
            }
        )

        # Create the delivery carrier with the required product_id
        cls.carrier = cls.env["delivery.carrier"].create(
            {
                "name": "Test Carrier",
                "product_id": cls.delivery_product.id,  # Ensure product_id is set
                "delivery_type": "fixed",
            }
        )

    def test_server_env_fields(self):
        expected_fields = {"postlogistics_client_id", "postlogistics_client_secret"}
        carrier_fields = self.carrier._server_env_fields

        for field in expected_fields:
            self.assertIn(
                field, carrier_fields, f"Field {field} is missing in _server_env_fields"
            )

        self.assertTrue(
            isinstance(carrier_fields, dict),
            "_server_env_fields should return a dictionary",
        )
