# Copyright 2026 Moduon
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo.tests import Form
from odoo.tests.common import users

from odoo.addons.stock_customer_deposit.tests.common import (
    TestStockCustomerDepositCommon,
)


class TestDeliveryFeeDeposit(TestStockCustomerDepositCommon):
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
            }
        )
        cls.carrier = cls.env["delivery.carrier"].create(
            {
                "name": "Carrier with Fee",
                "delivery_type": "fixed",
                "product_id": cls.delivery_product.id,
                "fixed_price": 5.0,
                "fee_product_id": cls.fee_product.id,
            }
        )
        cls.env.company.one_delivery_fee_by_sale_order = False
        cls.env.company.one_delivery_fee_by_commercial_partner_day = False

    def _create_sale_order(self, partner=None, customer_deposit=False, products=None):
        so_form = Form(self.env["sale.order"])
        so_form.partner_id = partner or self.partner1
        so_form.warehouse_id = self.warehouse
        so_form.customer_deposit = customer_deposit
        for product, qty in (products or {self.productA: 1.0}).items():
            with so_form.order_line.new() as line:
                line.product_id = product
                line.product_uom_qty = qty
        sale = so_form.save()
        sale.carrier_id = self.carrier
        return sale

    def _validate_picking(self, picking):
        picking.action_confirm()
        picking.action_assign()
        picking.action_set_quantities_to_reservation()
        picking._action_done()

    @users("user_customer_deposit")
    def test_delivery_fee_applied_when_sale_makes_deposit(self):
        stock_dict = {self.productA: {False: 1.0}}
        self.update_availiable_quantity(stock_dict)
        # This is the paid shipment that moves goods into the customer deposit.
        sale = self._create_sale_order(customer_deposit=True)
        sale.action_confirm()
        self.assertFalse(sale.picking_ids.carrier_id)
        self._validate_picking(sale.picking_ids)
        fee_lines = sale.order_line.filtered("is_delivery_fee")
        self.assertEqual(len(fee_lines), 1)
        self.assertEqual(fee_lines.delivery_fee_picking_id, sale.picking_ids)

    @users("user_customer_deposit")
    def test_delivery_fee_not_applied_when_delivering_deposit(self):
        stock_dict = {self.productA: {self.partner1: 1.0}}
        self.update_availiable_quantity(stock_dict)
        sale = self._create_sale_order()
        sale.action_confirm()

        # Existing customer-owned stock is already a deposit, even without routes.
        self._validate_picking(sale.picking_ids)

        self.assertFalse(sale.order_line.filtered("is_delivery_fee"))

    @users("user_customer_deposit")
    def test_delivery_fee_not_applied_on_successive_existing_deposit_deliveries(self):
        stock_dict = {self.productA: {self.partner1: 2.0}}
        self.update_availiable_quantity(stock_dict)

        for _dummy in range(2):
            sale = self._create_sale_order()
            sale.action_confirm()
            # Pre-existing deposits may be released in several deliveries.
            self._validate_picking(sale.picking_ids)
            self.assertFalse(sale.order_line.filtered("is_delivery_fee"))

    @users("user_customer_deposit")
    def test_delivery_fee_applied_to_mixed_deposit_delivery(self):
        stock_dict = {
            self.productA: {self.partner1: 1.0},
            self.productB: {False: 1.0},
        }
        self.update_availiable_quantity(stock_dict)
        sale = self._create_sale_order(
            products={self.productA: 1.0, self.productB: 1.0}
        )
        sale.action_confirm()
        # Mixed deliveries still need a fee because regular stock is shipped too.
        # Some flows do not propagate the sale carrier to this mixed picking.
        sale.picking_ids.carrier_id = False
        self.assertFalse(sale.picking_ids.carrier_id)
        self._validate_picking(sale.picking_ids)
        self.assertFalse(sale.picking_ids._is_full_customer_deposit_delivery())
        fee_lines = sale.order_line.filtered("is_delivery_fee")
        self.assertEqual(len(fee_lines), 1)
        self.assertEqual(fee_lines.delivery_fee_picking_id, sale.picking_ids)
