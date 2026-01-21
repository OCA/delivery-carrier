# Copyright 2026 Moduon
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
from odoo import Command
from odoo.tests import Form, TransactionCase


class DeliveryFeeTestCase(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.delivery_product = cls.env["product.product"].create(
            {
                "name": "Delivery test",
                "type": "service",
                "list_price": 5.0,
            }
        )
        cls.fee_product = cls.env["product.product"].create(
            {
                "name": "Delivery Fee Test",
                "type": "service",
                "list_price": 2.0,
                "description_sale": "Delivery fee charged per shipment",
            }
        )
        cls.carrier_with_fee = cls.env["delivery.carrier"].create(
            {
                "name": "Carrier with Fee",
                "delivery_type": "fixed",
                "product_id": cls.delivery_product.id,
                "fixed_price": 5.0,
                "fee_product_id": cls.fee_product.id,
            }
        )
        cls.carrier_without_fee = cls.env["delivery.carrier"].create(
            {
                "name": "Carrier without Fee",
                "delivery_type": "fixed",
                "product_id": cls.delivery_product.id,
                "fixed_price": 5.0,
            }
        )
        cls.product = cls.env["product.product"].create(
            {
                "name": "Test Product",
                "type": "consu",
                "list_price": 100.0,
            }
        )
        cls.customer = cls.env["res.partner"].create({"name": "Mr. Odoo"})
        cls.exempt_customer = cls.env["res.partner"].create(
            {
                "name": "Mrs. Exempted",
                "delivery_fee_exemption": True,
            }
        )
        cls.sale_order = cls.env["sale.order"].create(
            {
                "partner_id": cls.customer.id,
                "order_line": [
                    Command.create(
                        {
                            "product_id": cls.product.id,
                            "product_uom_qty": 1,
                            "price_unit": 100.0,
                        }
                    ),
                ],
            }
        )

    def test_delivery_fee_added_on_picking_validation(self):
        """Test that delivery fee is added when picking is validated"""
        self.sale_order.carrier_id = self.carrier_with_fee
        self.sale_order.action_confirm()
        picking = self.sale_order.picking_ids
        picking.action_set_quantities_to_reservation()
        picking._action_done()
        fee_lines = self.sale_order.order_line.filtered("is_delivery_fee")
        self.assertEqual(len(fee_lines), 1)
        self.assertEqual(fee_lines.price_unit, 2.0)
        # TODO: test render
        # TODO: test invoice
        # TODO: test multiple fees

    def test_no_fee_for_carrier_without_fee_product(self):
        """Test that no fee is added if carrier has no fee product"""
        self.sale_order.carrier_id = self.carrier_without_fee
        self.sale_order.action_confirm()
        picking = self.sale_order.picking_ids
        picking.move_ids.quantity_done = 1
        picking._action_done()
        fee_lines = self.sale_order.order_line.filtered("is_delivery_fee")
        self.assertEqual(len(fee_lines), 0)

    def test_exempt_customer_no_fee(self):
        """Test that exempt customers don't get charged delivery fees"""
        so_form = Form(self.sale_order)
        so_form.partner_id = self.exempt_customer
        so_form.save()
        self.sale_order.carrier_id = self.carrier_with_fee
        self.sale_order.action_confirm()
        picking = self.sale_order.picking_ids
        picking.move_ids.quantity_done = 1
        picking._action_done()
        fee_lines = self.sale_order.order_line.filtered("is_delivery_fee")
        self.assertEqual(len(fee_lines), 0)
