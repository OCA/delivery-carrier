# Copyright 2018 Simone Rubino - Agile Business Group
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests import common


class TestDeliveryCost(common.TransactionCase):

    def setUp(self):
        super(TestDeliveryCost, self).setUp()
        self.SaleOrder = self.env['sale.order']
        self.SaleOrderLine = self.env['sale.order.line']

        self.partner_18 = self.env.ref('base.res_partner_18')
        self.pricelist = self.env.ref('product.list0')
        self.product_4 = self.env.ref('product.product_product_4')
        self.product_uom_unit = self.env.ref('product.product_uom_unit')
        self.untaxed_delivery = self.env.ref(
            'delivery_price_rule_untaxed.untaxed_delivery_carrier')

    def test_untaxed(self):
        self.sale_untaxed_delivery_charges = self.SaleOrder.create({
            'partner_id': self.partner_18.id,
            'partner_invoice_id': self.partner_18.id,
            'partner_shipping_id': self.partner_18.id,
            'pricelist_id': self.pricelist.id,
            'order_line': [(0, 0, {
                'name': 'PC Assamble + 2GB RAM',
                'product_id': self.product_4.id,
                'product_uom_qty': 1,
                'product_uom': self.product_uom_unit.id,
                'price_unit': 1250.00,
            })],
            'carrier_id': self.untaxed_delivery.id
        })

        # Check if max value is working based on untaxed amount
        self.sale_untaxed_delivery_charges.get_delivery_price()
        self.assertEqual(
            self.sale_untaxed_delivery_charges.delivery_price, 0
        )

        self.sale_untaxed_delivery_charges.order_line.price_unit = 300

        # Add untaxed delivery cost in sale order
        self.sale_untaxed_delivery_charges.get_delivery_price()
        self.sale_untaxed_delivery_charges.set_delivery_line()

        # Check sale order after adding delivery cost
        line = self.SaleOrderLine.search([
            ('order_id', '=', self.sale_untaxed_delivery_charges.id),
            ('product_id', '=',
             self.sale_untaxed_delivery_charges.carrier_id.product_id.id)])

        self.assertEqual(len(line), 1,
                         "Delivery cost is not Added")
        self.assertEqual(line.price_subtotal, 600,
                         "Delivery cost does not correspond.")

        # Recalculate delivery price and line
        self.sale_untaxed_delivery_charges.get_delivery_price()
        self.sale_untaxed_delivery_charges.set_delivery_line()

        line = self.SaleOrderLine.search([
            ('order_id', '=', self.sale_untaxed_delivery_charges.id),
            ('product_id', '=',
             self.sale_untaxed_delivery_charges.carrier_id.product_id.id)])

        # Check if the delivery line is changed by the delivery line itself
        self.assertEqual(
            line.price_subtotal, 600,
            "Delivery line changed after adding the delivery line."
        )
        # Check if the delivery price is changed by the delivery line itself
        self.assertEqual(
            self.sale_untaxed_delivery_charges.delivery_price, 2 * 300,
            "Delivery price changed after adding the delivery line."
        )
