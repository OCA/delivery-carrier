# Copyright 2019 Vicent Cubells <vicent.cubells@tecnativa.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo.tests.common import SavepointCase


class TestDeliveryFreeFeeRemoval(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super(TestDeliveryFreeFeeRemoval, cls).setUpClass()

        product = cls.env['product.product'].create({
            'name': 'Product',
            'type': 'product',
        })
        product_delivery = cls.env['product.product'].create({
            'name': 'Delivery Product',
            'type': 'service',
        })
        cls.delivery_free = cls.env['delivery.carrier'].create({
            'name': 'Delivery Free',
            'delivery_type': 'fixed',
            'fixed_price': 0,
            'free_over': True,
            'product_id': product_delivery.id,
        })
        cls.delivery_with_charges = cls.env['delivery.carrier'].create({
            'name': 'Delivery With Charges',
            'delivery_type': 'fixed',
            'fixed_price': 100.0,
            'product_id': product_delivery.id,
        })
        partner = cls.env['res.partner'].create({
            'name': 'Test Partner',
        })
        cls.sale = cls.env['sale.order'].create({
            'partner_id': partner.id,
            'order_line': [(0, 0, {
                'product_id': product.id,
                'product_uom_qty': 1,
                'product_uom': product.uom_id.id,
                'price_unit': 3.0,
            })]
        })

    def test_delivery_free_fee_removal(self):
        self.sale.carrier_id = self.delivery_with_charges
        self.sale.delivery_rating_success = True
        self.sale.set_delivery_line()
        self.assertEqual(len(self.sale.mapped('order_line').filtered(
            lambda x: x.is_delivery)), 1)
        self.sale.carrier_id = self.delivery_free
        self.sale.set_delivery_line()
        self.assertEqual(len(self.sale.mapped('order_line').filtered(
            lambda x: x.is_delivery)), 0)
