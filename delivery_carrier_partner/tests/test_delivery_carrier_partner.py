from odoo.tests.common import TransactionCase


class TestDeliveryCarrierPartner(TransactionCase):
    def setUp(self):
        super().setUp()

        self.partner = self.env["res.partner"].create(
            {
                "name": "Transporter Test",
                "email": "transporter@test.com",
            }
        )

        self.product = self.env["product.product"].create(
            {
                "name": "Product Test",
            }
        )

        self.delivery_carrier = self.env["delivery.carrier"].create(
            {
                "name": "Carrier Test",
                "product_id": self.product.id,
                "partner_id": self.partner.id,
            }
        )

    def test_partner_association(self):
        """Test to verify the correct association of a partner with a carrier."""
        self.assertEqual(
            self.delivery_carrier.partner_id.id,
            self.partner.id,
            "The partner was not correctly associated with the delivery carrier.",
        )
