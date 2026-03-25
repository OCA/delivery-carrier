# Copyright 2026 Tecnativa - Carlos Lopez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command

from odoo.addons.base.tests.common import BaseCommon


class TestDeliveryCarrierMaxQuantity(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create({"name": "Test Partner"})
        cls.product1 = cls.env["product.product"].create({"name": "Test Product 1"})
        cls.carrier = cls.env["delivery.carrier"].create(
            {
                "name": "Test Carrier with Limit",
                "delivery_type": "fixed",
                "product_id": cls.env.ref("delivery.product_product_delivery").id,
                "fixed_price": 10.0,
                "max_quantity": 5.0,  # Set max quantity to 5
            }
        )
        cls.sale_order = cls.env["sale.order"].create(
            {
                "partner_id": cls.partner.id,
                "order_line": [
                    Command.create(
                        {
                            "product_id": cls.product1.id,
                            "product_uom_qty": 5.0,
                        }
                    ),
                ],
            }
        )

    def test_carrier_available(self):
        is_available = self.carrier._match(self.partner, self.sale_order)
        self.assertTrue(is_available)
        self.sale_order.order_line.product_uom_qty = 6.0  # Exceed max quantity
        is_available = self.carrier._match(self.partner, self.sale_order)
        self.assertFalse(is_available)
