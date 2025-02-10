# Copyright 2023 Moduon Team S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)


from odoo import Command
from odoo.tests.common import TransactionCase


class TestDeliveryDriverStockPickingBatch(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner_test = cls.env["res.partner"].create({"name": "My Test Customer"})
        cls.driver_test_1 = cls.env["res.partner"].create({"name": "My Test Driver 1"})
        cls.driver_test_2 = cls.env["res.partner"].create({"name": "My Test Driver 2"})
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
        cls.delivery_test_1 = cls.env["delivery.carrier"].create(
            {
                "name": "Normal Delivery Charges",
                "fixed_price": 10,
                "delivery_type": "fixed",
                "product_id": cls.product_delivery_test.id,
                "driver_id": cls.driver_test_1.id,
            }
        )
        cls.delivery_test_2 = cls.env["delivery.carrier"].create(
            {
                "name": "Normal Delivery Charges 2",
                "fixed_price": 10,
                "delivery_type": "fixed",
                "product_id": cls.product_delivery_test.id,
                "driver_id": cls.driver_test_2.id,
            }
        )

    def test_delivery_driver_stock_picking_batch(self):
        """Check Drivers in stock picking batch."""
        picking_1 = self.env["stock.picking"].create(
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
                "carrier_id": self.delivery_test_1.id,
            }
        )
        picking_2 = self.env["stock.picking"].create(
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
                "carrier_id": self.delivery_test_2.id,
            }
        )
        batch = self.env["stock.picking.batch"].create(
            {
                "name": "Test Batch",
                "picking_ids": [(4, picking_1.id), (4, picking_2.id)],
            }
        )
        self.assertEqual(batch.driver_ids, self.driver_test_1 | self.driver_test_2)
        batch.write({"picking_ids": [(3, picking_2.id)]})
        self.assertEqual(batch.driver_ids, self.driver_test_1)
        batch.write({"picking_ids": [(4, picking_2.id)]})
        picking_2.write({"carrier_id": self.delivery_test_1.id})
        self.assertEqual(batch.driver_ids, self.driver_test_1)
