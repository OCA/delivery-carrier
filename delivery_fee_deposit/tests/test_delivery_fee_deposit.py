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
            {"name": "Delivery test", "type": "service", "list_price": 5.0}
        )
        cls.fee_product = cls.env["product.product"].create(
            {"name": "Delivery Fee Test", "type": "service", "list_price": 2.0}
        )
        cls.carrier = cls.env["delivery.carrier"].create(
            {
                "name": "Carrier with Fee",
                "delivery_type": "fixed",
                "product_id": cls.delivery_product.id,
                "fixed_price": 5.0,
                "fee_product_id": cls.fee_product.id,
                "fee_return_percentage": 75,
            }
        )
        # Ensure compatibility with sale_order_warehouse_from_delivery_carrier in CI
        if "so_warehouse_id" in cls.carrier._fields:
            cls.carrier.so_warehouse_id = cls.warehouse
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
        for move in picking.move_ids:
            move.quantity = move.product_uom_qty
        picking.button_validate()

    def _return_picking(self, picking, product=None):
        return_wizard = Form(
            self.env["stock.return.picking"].with_context(
                active_ids=picking.ids,
                active_id=picking.id,
                active_model="stock.picking",
            )
        ).save()
        if product:
            for line in return_wizard.product_return_moves:
                line.quantity = (
                    line.move_id.quantity if line.product_id == product else 0
                )
        elif not any(return_wizard.product_return_moves.mapped("quantity")):
            for line in return_wizard.product_return_moves:
                line.quantity = line.move_id.quantity
        return_action = return_wizard.action_create_returns()
        return_pick = self.env["stock.picking"].browse(return_action["res_id"])
        self._validate_picking(return_pick)
        return return_pick

    @users("user_customer_deposit")
    def test_delivery_fee_applied_when_sale_makes_deposit(self):
        self.update_available_quantity({self.productA: {False: 1.0}})
        sale = self._create_sale_order(customer_deposit=True)
        sale.action_confirm()
        self.assertFalse(sale.picking_ids.carrier_id)
        self._validate_picking(sale.picking_ids)
        fee_lines = sale.order_line.filtered("is_delivery_fee")
        self.assertEqual(len(fee_lines), 1)
        self.assertEqual(fee_lines.delivery_fee_picking_id, sale.picking_ids)

    @users("user_customer_deposit")
    def test_delivery_fee_reimbursed_when_deposit_creation_is_returned(self):
        self.update_available_quantity({self.productA: {False: 1.0}})
        sale = self._create_sale_order(customer_deposit=True)
        sale.action_confirm()
        self._validate_picking(sale.picking_ids)
        fee_lines = sale.order_line.filtered("is_delivery_fee")
        self._return_picking(sale.picking_ids)
        self.assertEqual(fee_lines.product_uom_qty, 0.25)

    @users("user_customer_deposit")
    def test_no_fee_for_full_customer_deposit_delivery(self):
        self.update_available_quantity({self.productA: {self.partner1: 1.0}})
        sale = self._create_sale_order()
        sale.action_confirm()
        self._validate_picking(sale.picking_ids)
        self.assertTrue(sale.picking_ids._delivery_fee_deposit_is_full_delivery())
        self.assertFalse(sale.order_line.filtered("is_delivery_fee"))

    @users("user_customer_deposit")
    def test_no_fee_for_successive_existing_deposit_deliveries(self):
        self.update_available_quantity({self.productA: {self.partner1: 2.0}})
        for _dummy in range(2):
            sale = self._create_sale_order()
            sale.action_confirm()
            self._validate_picking(sale.picking_ids)
            self.assertFalse(sale.order_line.filtered("is_delivery_fee"))

    @users("user_customer_deposit")
    def test_delivery_fee_applied_to_mixed_deposit_delivery(self):
        sale = self._create_mixed_deposit_delivery()
        fee_lines = sale.order_line.filtered("is_delivery_fee")
        self.assertEqual(len(fee_lines), 1)
        self.assertEqual(fee_lines.delivery_fee_picking_id, sale.picking_ids)

    @users("user_customer_deposit")
    def test_mixed_deposit_delivery_keeps_day_limit(self):
        self.env.company.sudo().one_delivery_fee_by_commercial_partner_day = True
        self.update_available_quantity({self.productB: {False: 1.0}})
        sale = self._create_sale_order(products={self.productB: 1.0})
        sale.action_confirm()
        self._validate_picking(sale.picking_ids)
        self.assertEqual(len(sale.order_line.filtered("is_delivery_fee")), 1)

        mixed_sale = self._create_mixed_deposit_delivery()
        self.assertFalse(mixed_sale.order_line.filtered("is_delivery_fee"))

    @users("user_customer_deposit")
    def test_full_deposit_delivery_does_not_count_for_day_limit(self):
        self.env.company.sudo().one_delivery_fee_by_commercial_partner_day = True
        deposit_sale = self._create_full_deposit_delivery()
        self.assertFalse(deposit_sale.order_line.filtered("is_delivery_fee"))

        mixed_sale = self._create_mixed_deposit_delivery()
        self.assertEqual(len(mixed_sale.order_line.filtered("is_delivery_fee")), 1)

    @users("user_customer_deposit")
    def test_mixed_deposit_returning_only_deposit_product_keeps_fee(self):
        sale = self._create_mixed_deposit_delivery()
        fee_lines = sale.order_line.filtered("is_delivery_fee")
        self._return_picking(sale.picking_ids, product=self.productA)
        self.assertEqual(fee_lines.product_uom_qty, 1)

    @users("user_customer_deposit")
    def test_mixed_deposit_returning_regular_product_reimburses_fee(self):
        sale = self._create_mixed_deposit_delivery()
        fee_lines = sale.order_line.filtered("is_delivery_fee")
        self._return_picking(sale.picking_ids, product=self.productB)
        self.assertEqual(fee_lines.product_uom_qty, 0.25)

    def _create_mixed_deposit_delivery(self):
        self.update_available_quantity(
            {
                self.productA: {self.partner1: 1.0},
                self.productB: {False: 1.0},
            }
        )
        sale = self._create_sale_order(
            products={self.productA: 1.0, self.productB: 1.0}
        )
        sale.action_confirm()
        sale.picking_ids.carrier_id = False
        self._validate_picking(sale.picking_ids)
        self.assertFalse(sale.picking_ids._delivery_fee_deposit_is_full_delivery())
        return sale

    def _create_full_deposit_delivery(self):
        self.update_available_quantity({self.productA: {self.partner1: 1.0}})
        sale = self._create_sale_order()
        sale.action_confirm()
        self._validate_picking(sale.picking_ids)
        self.assertTrue(sale.picking_ids._delivery_fee_deposit_is_full_delivery())
        return sale
