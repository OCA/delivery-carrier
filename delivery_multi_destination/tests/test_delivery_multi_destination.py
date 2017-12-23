# -*- coding: utf-8 -*-
# Copyright 2017 Luis M. Ontalba <luis.martinez@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp.tests import common


class TestDeliveryMultiDestination(common.SavepointCase):
    @classmethod
    def setUpClass(cls):
        super(TestDeliveryMultiDestination, cls).setUpClass()
        cls.country_1 = cls.env['res.country'].create({
            'name': 'Test country 1',
        })
        cls.partner_1 = cls.env['res.partner'].create({
            'name': 'Test partner 1',
            'country_id': cls.country_1.id,
        })
        cls.country_2 = cls.env['res.country'].create({
            'name': 'Test country 2',
        })
        cls.state = cls.env['res.country.state'].create({
            'name': 'Test state',
            'code': 'TS',
            'country_id': cls.country_2.id,
        })
        cls.partner_2 = cls.env['res.partner'].create({
            'name': 'Test partner 2',
            'country_id': cls.country_2.id,
            'state_id': cls.state.id,
            'zip': '22222'
        })
        cls.partner_3 = cls.env['res.partner'].create({
            'name': 'Test partner 3',
            'country_id': cls.country_2.id,
            'state_id': cls.state.id,
            'zip': '33333'
        })
        cls.carrier_multi = cls.env['delivery.carrier'].create({
            'name': 'Test carrier multi',
            'destination_type': 'multi',
            'delivery_type': 'fixed',
            'fixed_price': 100,
            'child_ids': [
                (0, 0, {
                    'name': 'Test child 1',
                    'sequence': 1,
                    'country_ids': [(6, 0, cls.country_2.ids)],
                    'state_ids': [(6, 0, cls.state.ids)],
                    'zip_from': 20000,
                    'zip_to': 29999,
                    'delivery_type': 'fixed',
                    'fixed_price': 50,
                }),
                (0, 0, {
                    'name': 'Test child 2',
                    'sequence': 2,
                    'country_ids': [(6, 0, cls.country_2.ids)],
                    'state_ids': [(6, 0, cls.state.ids)],
                    'zip_from': 30000,
                    'zip_to': 39999,
                    'delivery_type': 'fixed',
                    'fixed_price': 150,
                })
            ]
        })
        cls.carrier_single = cls.carrier_multi.copy({
            'name': 'Test carrier single',
            'destination_type': 'one',
            'child_ids': False,
        })
        cls.product = cls.env['product.product'].create({
            'name': 'Test product',
        })
        cls.sale_order = cls.env['sale.order'].create({
            'partner_id': cls.partner_1.id,
            'picking_policy': 'direct',
            'order_line': [
                (0, 0, {
                    'name': 'Test',
                    'product_id': cls.product.id,
                    'product_uom_qty': 1,
                    'price_unit': 1,
                }),
            ]
        })

    def test_delivery_multi_destination(self):
        order = self.sale_order
        order.carrier_id = self.carrier_single.id
        self.assertAlmostEqual(order.delivery_price, 100, 2)
        order.carrier_id = self.carrier_multi.id
        order.invalidate_cache()
        order.partner_shipping_id = self.partner_2.id
        order.delivery_set()
        self.assertAlmostEqual(order.delivery_price, 50, 2)
        order.invalidate_cache()
        order.partner_shipping_id = self.partner_3.id
        order.delivery_set()
        self.assertAlmostEqual(order.delivery_price, 150, 2)

    def test_search(self):
        carriers = self.env['delivery.carrier'].search([])
        children_carrier = self.carrier_multi.with_context(
            show_children_carriers=True,
        ).child_ids[0]
        self.assertNotIn(children_carrier, carriers)

    def test_name_search(self):
        carrier_names = self.env['delivery.carrier'].name_search()
        children_carrier = self.carrier_multi.with_context(
            show_children_carriers=True,
        ).child_ids[0]
        self.assertTrue(
            all(x[0] != children_carrier.id for x in carrier_names)
        )
