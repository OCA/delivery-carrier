# Copyright 2025 BizzAppDev Systems Pvt. Ltd.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields

from .common import TestPostlogisticsCommon


class TestStockMove(TestPostlogisticsCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        res_partner_env = cls.env["res.partner"]
        product_env = cls.env["product.product"]
        sale_order_env = cls.env["sale.order"]
        sale_order_line_env = cls.env["sale.order.line"]
        stock_picking_env = cls.env["stock.picking"]
        stock_move_env = cls.env["stock.move"]
        cls.partner = res_partner_env.create(
            {
                "name": "Test Partner",
                "type": "delivery",
                "street": "123 Test St.",
                "city": "Test City",
                "zip": 234567,
                "country_id": cls.env.ref("base.us").id,
            }
        )

        cls.product = product_env.create(
            {
                "name": "Test Product",
                "uom_id": cls.env.ref("uom.product_uom_unit").id,
            }
        )

        cls.sale_order = sale_order_env.create(
            {
                "partner_id": cls.partner.id,
                "commitment_date": fields.Datetime.now(),
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": cls.env.ref("product.product_product_1").id,
                            "product_uom_qty": 1,
                            "price_unit": 100,
                        },
                    )
                ],
            }
        )

        cls.sale_order_line = sale_order_line_env.create(
            {
                "order_id": cls.sale_order.id,
                "product_id": cls.product.id,
                "product_uom_qty": 1,
                "price_unit": 100,
            }
        )

        cls.picking = stock_picking_env.create(
            {
                "name": "Test Picking",
                "sale_id": cls.sale_order.id,
                "partner_id": cls.partner.id,
                "picking_type_id": cls.env.ref("stock.picking_type_out").id,
                "delivery_type": "postlogistics",
            }
        )

        cls.stock_move = stock_move_env.create(
            {
                "name": "Test Stock Move",
                "product_id": cls.product.id,
                "product_uom_qty": 1,
                "product_uom": cls.product.uom_id.id,
                "sale_line_id": cls.sale_order_line.id,
                "picking_id": cls.picking.id,
                "location_id": cls.env.ref("stock.stock_location_stock").id,
                "location_dest_id": cls.env.ref("stock.stock_location_customers").id,
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
