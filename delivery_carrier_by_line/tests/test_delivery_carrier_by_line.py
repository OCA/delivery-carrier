# Copyright 2021 Camptocamp
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import Form, SavepointCase
from odoo.tools import mute_logger


class TestPackageFee(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.product1 = cls.env["product.product"].create(
            {"name": "Product 1", "type": "product", "lst_price": 1.0}
        )
        cls.product2 = cls.env["product.product"].create(
            {"name": "Product 2", "type": "product", "lst_price": 1.0}
        )
        cls.product3 = cls.env["product.product"].create(
            {"name": "Product 3", "type": "product", "lst_price": 1.0}
        )
        cls.partner = cls.env["res.partner"].create({"name": "Partner"})
        product_delivery = cls.env["product.product"].create(
            {"name": "Delivery Product", "type": "service"}
        )
        cls.carrier1 = cls.env["delivery.carrier"].create(
            {
                "name": "Delivery 1",
                "fixed_price": 10.0,
                "product_id": product_delivery.id,
            }
        )
        cls.carrier2 = cls.env["delivery.carrier"].create(
            {
                "name": "Delivery 1",
                "fixed_price": 10.0,
                "product_id": product_delivery.id,
            }
        )
        cls.sale = cls._create_sale()
        # carrier added with delivery_auto_refresh addon which installed previously
        # force it to empty
        cls.sale.carrier_id = False

    @classmethod
    def _create_sale(cls):
        sale_form = Form(cls.env["sale.order"])
        sale_form.partner_id = cls.partner
        with mute_logger("odoo.tests.common.onchange"):
            with sale_form.order_line.new() as line:
                line.product_id = cls.product1
                line.product_uom_qty = 10.0
            with sale_form.order_line.new() as line:
                line.product_id = cls.product2
                line.product_uom_qty = 10.0
            with sale_form.order_line.new() as line:
                line.product_id = cls.product3
                line.product_uom_qty = 10.0
        return sale_form.save()

    def test_no_carrier(self):
        self.sale.action_confirm()
        picking = self.sale.picking_ids
        self.assertEqual(len(picking), 1)
        self.assertFalse(picking.carrier_id)

    def test_one_carrier(self):
        self.sale.order_line.write({"carrier_id": self.carrier1.id})
        self.sale.action_confirm()
        picking = self.sale.picking_ids
        self.assertEqual(len(picking), 1)
        self.assertEqual(picking.carrier_id, self.carrier1)

    def test_two_carrier(self):
        self.sale.order_line[0].write({"carrier_id": self.carrier1.id})
        self.sale.order_line[1].write({"carrier_id": self.carrier2.id})
        self.sale.order_line[2].write({"carrier_id": self.carrier2.id})
        self.sale.action_confirm()
        picking_1 = self.sale.picking_ids.filtered(
            lambda pick: pick.carrier_id == self.carrier1
        )
        picking_2 = self.sale.picking_ids.filtered(
            lambda pick: pick.carrier_id == self.carrier2
        )
        self.assertEqual(len(self.sale.picking_ids), 2)
        self.assertEqual(picking_1.carrier_id, self.carrier1)
        self.assertEqual(picking_2.carrier_id, self.carrier2)
        self.assertEqual(len(picking_1.move_lines), 1)
        self.assertEqual(len(picking_2.move_lines), 2)

    def test_three_carrier(self):
        self.sale.order_line[0].write({"carrier_id": self.carrier1.id})
        self.sale.order_line[1].write({"carrier_id": self.carrier2.id})
        self.sale.action_confirm()
        picking_1 = self.sale.picking_ids.filtered(
            lambda pick: pick.carrier_id == self.carrier1
        )
        picking_2 = self.sale.picking_ids.filtered(
            lambda pick: pick.carrier_id == self.carrier2
        )
        picking_3 = self.sale.picking_ids.filtered(lambda pick: not pick.carrier_id)
        self.assertEqual(len(self.sale.picking_ids), 3)
        self.assertEqual(picking_1.carrier_id, self.carrier1)
        self.assertEqual(picking_2.carrier_id, self.carrier2)
        self.assertFalse(picking_3.carrier_id)
        self.assertEqual(len(picking_1.move_lines), 1)
        self.assertEqual(len(picking_2.move_lines), 1)
        self.assertEqual(len(picking_3.move_lines), 1)
