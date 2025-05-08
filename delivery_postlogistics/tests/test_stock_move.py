# Copyright 2025 BizzAppDev Systems Pvt. Ltd.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields

from .common import TestPostlogisticsCommon


class TestStockMove(TestPostlogisticsCommon):
    def setUp(self):
        super().setUp()
        res_partner_env = self.env["res.partner"]
        product_env = self.env["product.product"]
        sale_order_env = self.env["sale.order"]
        sale_order_line_env = self.env["sale.order.line"]
        stock_picking_env = self.env["stock.picking"]
        stock_move_env = self.env["stock.move"]
        self.partner = res_partner_env.create(
            {
                "name": "Test Partner",
                "type": "delivery",
                "street": "123 Test St.",
                "city": "Test City",
                "zip": 234567,
                "country_id": self.env.ref("base.us").id,
            }
        )

        self.product = product_env.create(
            {
                "name": "Test Product",
                "uom_id": self.env.ref("uom.product_uom_unit").id,
            }
        )

        self.sale_order = sale_order_env.create(
            {
                "partner_id": self.partner.id,
                "commitment_date": fields.Datetime.now(),
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.env.ref("product.product_product_1").id,
                            "product_uom_qty": 1,
                            "price_unit": 100,
                        },
                    )
                ],
            }
        )

        self.sale_order_line = sale_order_line_env.create(
            {
                "order_id": self.sale_order.id,
                "product_id": self.product.id,
                "product_uom_qty": 1,
                "price_unit": 100,
            }
        )

        self.picking = stock_picking_env.create(
            {
                "name": "Test Picking",
                "sale_id": self.sale_order.id,
                "partner_id": self.partner.id,
                "picking_type_id": self.env.ref("stock.picking_type_out").id,
                "delivery_type": "postlogistics",
            }
        )

        self.stock_move = stock_move_env.create(
            {
                "name": "Test Stock Move",
                "product_id": self.product.id,
                "product_uom_qty": 1,
                "product_uom": self.product.uom_id.id,
                "sale_line_id": self.sale_order_line.id,
                "picking_id": self.picking.id,
                "location_id": self.env.ref("stock.stock_location_stock").id,
                "location_dest_id": self.env.ref("stock.stock_location_customers").id,
            }
        )

    def test_get_new_picking_values(self):
        """Test if 'delivery_fixed_date' is included in the stock move values for a
        new picking."""
        stock_move_vals = self.stock_move._get_new_picking_values()
        self.assertIn(
            "delivery_fixed_date",
            stock_move_vals,
            "The 'delivery_fixed_date' should be present in the returned values.",
        )

    def test_cod_amount_no_sale_order(self):
        """Test COD amount when picking has no linked sale order."""
        picking = self.picking.create(
            {
                "partner_id": self.env.ref("base.res_partner_1").id,
                "location_id": self.env.ref("stock.stock_location_stock").id,
                "location_dest_id": self.env.ref("stock.stock_location_customers").id,
                "picking_type_id": self.env.ref("stock.picking_type_out").id,
            }
        )
        self.assertEqual(
            picking.postlogistics_cod_amount(),
            0.0,
            "COD amount should be 0.0 when no sale order is linked to the picking.",
        )

    def test_cod_amount_single_order_and_picking(self):
        """Test COD amount for a single sale order and picking."""
        self.picking.sale_id = self.sale_order
        self.assertEqual(
            self.picking.postlogistics_cod_amount(),
            self.sale_order.amount_total,
            "The COD amount should match the total amount of the sale order.",
        )
