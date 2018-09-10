# -*- coding: utf-8 -*-
# Copyright 2018 Simone Rubino - Agile Business Group
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests import common
from odoo.tools import float_compare


class TestPriceByCategory(common.TransactionCase):

    def setUp(self):
        super(TestPriceByCategory, self).setUp()
        self.sale_order_model = self.env['sale.order']
        self.sale_order_line_model = self.env['sale.order.line']
        self.product_category_model = self.env['product.category']
        self.delivery_price_rule_model = self.env['delivery.price.rule']

        self.partner = self.env.ref('base.res_partner_1')
        self.product = self.env.ref('product.product_product_1')
        self.normal_delivery = self.env.ref('delivery.normal_delivery_carrier')
        self.sale_order = self.sale_order_model.create({
            'partner_id': self.partner.id,
            'partner_invoice_id': self.partner.id,
            'partner_shipping_id': self.partner.id,
            'order_line': [(0, 0, {
                'name': 'PC Assamble + 2GB RAM',
                'product_id': self.product.id,
                'product_uom_qty': 1,
                'product_uom': self.product.uom_id.id,
                'price_unit': 750.00,
            })],
            'carrier_id': self.normal_delivery.id
        })
        rule_values = dict(
            sequence=-1,
            max_value=0.0,
            carrier_id=self.normal_delivery.id,
            product_category_id=self.product.categ_id.id,
            product_category_price=500.00)
        self.category_rule = self.delivery_price_rule_model.create(rule_values)

    def test_category_price_rule(self):
        """Match category rule is matched if it is first"""
        self.sale_order.delivery_set()

        # Check that the delivery line has been added
        line = self.sale_order_line_model.search(
            [('order_id', '=', self.sale_order.id),
             ('product_id', '=', self.normal_delivery.product_id.id)])
        self.assertEqual(len(line), 1, "Delivery cost is not Added")

        # Check that delivery line has correct price
        self.assertEqual(float_compare(
            line.price_subtotal,
            self.category_rule.product_category_price, precision_digits=2), 0,
            "Delivery cost does not correspond.")

    def test_category_price_rule_no_first(self):
        """Match category rule is not matched if it is last"""
        self.category_rule.sequence = 99

        self.sale_order.delivery_set()

        # Check that the delivery line has been added
        line = self.sale_order_line_model.search(
            [('order_id', '=', self.sale_order.id),
             ('product_id', '=', self.normal_delivery.product_id.id)])
        self.assertEqual(len(line), 1, "Delivery cost is not Added")

        # Check that delivery line has correct price
        self.assertEqual(float_compare(
            line.price_subtotal,
            self.category_rule.product_category_price, precision_digits=2), -1,
            "Delivery cost does not correspond.")

    def test_category_price_rule_no_match(self):
        """Do not match category rule if it has wrong category"""
        self.category_rule.product_category_id = \
            self.product_category_model.search([
                ('id', '!=', self.product.categ_id.id)], limit=1)

        self.sale_order.delivery_set()

        # Check that the delivery line has been added
        line = self.sale_order_line_model.search(
            [('order_id', '=', self.sale_order.id),
             ('product_id', '=', self.normal_delivery.product_id.id)])
        self.assertEqual(len(line), 1, "Delivery price is not Added")

        # Check that delivery line has correct price
        self.assertEqual(float_compare(
            line.price_subtotal,
            self.category_rule.product_category_price, precision_digits=2), -1,
            "Delivery price does not correspond.")
