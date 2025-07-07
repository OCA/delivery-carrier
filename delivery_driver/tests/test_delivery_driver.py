# Copyright 2024 Moduon Team S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)


from odoo import Command
from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestDeliverDriver(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner_test = cls.env["res.partner"].create({"name": "My Test Customer"})
        cls.driver_test = cls.env["res.partner"].create({"name": "My Test Driver"})
        cls.product_test = cls.env["product.product"].create(
            {"name": "A product to deliver"}
        )
        cls.product_delivery_test = cls.env["product.product"].create(
            {
                "name": "Normal Delivery Charges",
                "invoice_policy": "order",
                "type": "service",
                "list_price": 10.0,
                "categ_id": cls.env.ref("delivery.product_category_deliveries").id,
            }
        )
        cls.delivery_test = cls.env["delivery.carrier"].create(
            {
                "name": "Normal Delivery Charges",
                "fixed_price": 10,
                "delivery_type": "fixed",
                "product_id": cls.product_delivery_test.id,
                "driver_id": cls.driver_test.id,
            }
        )

    def test_partner_is_driver(self):
        self.assertTrue(self.driver_test.is_driver)
        self.assertFalse(self.partner_test.is_driver)
        with self.assertRaises(ValidationError):
            self.driver_test.write({"is_driver": False})
        self.delivery_test.write({"driver_id": self.partner_test.id})
        self.assertTrue(self.partner_test.is_driver)

    def test_sale_flow(self):
        sale_order = self.env["sale.order"].create(
            {
                "partner_id": self.partner_test.id,
                "partner_invoice_id": self.partner_test.id,
                "partner_shipping_id": self.partner_test.id,
                "order_line": [
                    Command.create(
                        {
                            "product_id": self.product_test.id,
                            "product_uom_qty": 1,
                            "product_uom": self.product_test.uom_id.id,
                            "price_unit": 100,
                        },
                    )
                ],
                "carrier_id": self.delivery_test.id,
            }
        )
        sale_order.action_confirm()
        self.assertEqual(sale_order.picking_ids.driver_id, self.driver_test)

    def test_stock_flow(self):
        stock_picking = self.env["stock.picking"].create(
            {
                "partner_id": self.partner_test.id,
                "picking_type_id": self.env.ref("stock.picking_type_out").id,
                "location_id": self.env.ref("stock.stock_location_stock").id,
                "location_dest_id": self.env.ref("stock.stock_location_customers").id,
                "move_ids": [
                    Command.create(
                        {
                            "name": "Test",
                            "product_id": self.product_test.id,
                            "product_uom_qty": 1,
                            "product_uom": self.product_test.uom_id.id,
                            "location_id": self.env.ref(
                                "stock.stock_location_stock"
                            ).id,
                            "location_dest_id": self.env.ref(
                                "stock.stock_location_customers"
                            ).id,
                        },
                    )
                ],
                "carrier_id": self.delivery_test.id,
            }
        )
        self.assertEqual(stock_picking.driver_id, self.driver_test)

    def test_get_name_with_show_driver_context(self):
        """Test _compute_display_name method when 'show_driver' is in the context."""
        driver_with_context = self.driver_test.with_context(show_driver=True)
        driver_with_context._compute_display_name()
        self.assertEqual(driver_with_context.display_name, "My Test Driver")

    def test_get_name_without_show_driver_context(self):
        """Test _compute_display_name method when 'show_driver' is NOT in the
        context."""
        self.driver_test._compute_display_name()
        self.assertTrue(self.driver_test.display_name)
