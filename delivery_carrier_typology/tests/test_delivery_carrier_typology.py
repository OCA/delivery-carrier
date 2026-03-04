# Copyright 2025 Akretion (https://www.akretion.com).
# @author Kévin Roche <kevin.roche@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import Form, TransactionCase


class TestDeliveryCarrierTypology(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.free = cls.env["product.product"].create(
            {
                "name": "Free Delivery Charges",
                "type": "service",
                "list_price": 0,
                "categ_id": cls.env.ref("delivery.product_category_deliveries").id,
            }
        )

        cls.free_delivery = cls.env["delivery.carrier"].create(
            {
                "name": "Free Delivery Charges",
                "delivery_type": "fixed",
                "fixed_price": 0,
                "product_id": cls.free.id,
            }
        )

        cls.free_typology = cls.env["delivery.carrier.typology"].create(
            {
                "name": "Free Delivery",
                "carrier_id": cls.free_delivery.id,
            }
        )

        cls.so = cls.env["sale.order"].create(
            {
                "partner_id": cls.env.ref("base.res_partner_1").id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": cls.env.ref("product.product_product_4").id,
                            "product_uom_qty": 1,
                            "price_unit": 10,
                        },
                    ),
                ],
            }
        )

    def test_choose_carrier_from_typology(self):
        wizard_ctx = self.so.action_open_delivery_wizard()["context"]
        delivery_wizard = Form(
            self.env["choose.delivery.carrier"].with_context(**wizard_ctx)
        )
        self.assertNotEqual(delivery_wizard.carrier_id, self.free_delivery)
        delivery_wizard.carrier_typology_id = self.free_typology
        self.assertEqual(delivery_wizard.carrier_id, self.free_delivery)
        delivery_wizard = delivery_wizard.save()
        delivery_wizard.button_confirm()
        self.assertEqual(self.so.carrier_id, self.free_delivery)
        self.assertTrue(
            self.so.order_line.filtered(
                lambda l: l.is_delivery and l.product_id == self.free
            )
        )
