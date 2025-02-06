# Copyright 2024 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo import Command
from odoo.tests import Form
from odoo.tests.common import TransactionCase


class TestDeliveryCarrierManualPrice(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        product_shipping_cost = cls.env["product.product"].create(
            {
                "type": "service",
                "name": "Shipping costs",
                "standard_price": 10,
                "list_price": 100,
            }
        )
        cls.carrier = cls.env["delivery.carrier"].create(
            {
                "name": "Test carrier",
                "delivery_type": "fixed",
                "product_id": product_shipping_cost.id,
                "fixed_price": 50,
                "is_manual_price": True,
            }
        )
        cls.product = cls.env["product.product"].create(
            {"name": "Test product", "type": "consu"}
        )
        cls.partner = cls.env["res.partner"].create({"name": "Test Partner"})
        cls.sale = cls.env["sale.order"].create(
            {
                "partner_id": cls.partner.id,
                "order_line": [
                    Command.create(
                        {
                            "product_id": cls.product.id,
                            "product_uom_qty": 1,
                            "price_unit": 10,
                        }
                    )
                ],
            }
        )

    def test_delivery_carrier_manual_price(self):
        delivery_wizard = Form(
            self.env["choose.delivery.carrier"].with_context(
                **{"default_order_id": self.sale.id, "default_carrier_id": self.carrier}
            )
        )
        choose_delivery_carrier = delivery_wizard.save()
        self.assertEqual(choose_delivery_carrier.delivery_price, 50)
        with Form(
            choose_delivery_carrier,
            view="delivery_carrier_manual_price.choose_delivery_carrier_view_form",
        ) as form:
            form.delivery_price = 70
        choose_delivery_carrier.button_confirm()
        delivery_lines = self.sale.order_line.filtered(lambda line: line.is_delivery)
        delivery_price = sum(delivery_lines.mapped("price_unit"))
        self.assertEqual(delivery_price, 70)
        self.assertEqual(len(delivery_lines), 1)
        # Modify sale line and check recompute_delivery_price
        line = self.sale.order_line.filtered(
            lambda line: line.product_id == self.product
        )
        line.price_unit = 20
        self.assertFalse(self.sale.recompute_delivery_price)
