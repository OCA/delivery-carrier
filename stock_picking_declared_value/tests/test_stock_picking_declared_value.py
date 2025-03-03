# Copyright 2025 Nitrokey GmbH
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase


class TestStockPickingDeclaredValue(TransactionCase):
    def setUp(self):
        super().setUp()
        # Create a product
        self.product = self.env["product.product"].create(
            {
                "name": "Test Product",
                "type": "product",
                "list_price": 100.0,
            }
        )
        # Create a customer
        self.partner = self.env["res.partner"].create(
            {
                "name": "Test Customer",
                "customer_rank": 1,
            }
        )
        # Create a delivery carrier with declared amount percentage
        self.carrier = self.env["delivery.carrier"].create(
            {
                "name": "Test Carrier",
                "delivery_type": "fixed",
                "product_id": self.product.id,
                "fixed_price": 10.0,
                "declared_amount": 80.0,
            }
        )
        # Create a sales order
        self.sale_order = self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "carrier_id": self.carrier.id,
            }
        )
        # Create a sales order line
        self.sale_order_line = self.env["sale.order.line"].create(
            {
                "order_id": self.sale_order.id,
                "product_id": self.product.id,
                "product_uom_qty": 5.0,
                "price_unit": 100.0,
                "discount": 10.0,
            }
        )

    def test_declared_value_copied_to_picking(self):
        """Test that declared values are copied from sale order to picking."""
        # Confirm the sales order
        self.sale_order.action_confirm()
        # Get the picking created from the sales order
        picking = self.sale_order.picking_ids[0]
        # Check that the picking has the sale_id field set
        self.assertEqual(picking.sale_id, self.sale_order)
        # Check that the move has the sale_unit_price and discount fields set
        move = picking.move_lines[0]
        self.assertEqual(move.sale_unit_price, 100.0)
        self.assertEqual(move.discount, 10.0)
        # Check that the move has the price_subtotal field set with discount applied
        # 100.0 * (1 - 10.0 / 100.0) * 5.0 = 90.0 * 5.0 = 450.0
        self.assertEqual(move.price_subtotal, 450.0)
        # Check that the picking has the declared_amount field set from carrier
        self.assertEqual(picking.declared_amount, 80.0)
        # Check that the picking has the amount_total field set with declared_amount applied
        # 450.0 * 80.0 / 100.0 = 360.0
        self.assertEqual(picking.amount_total, 360.0)
