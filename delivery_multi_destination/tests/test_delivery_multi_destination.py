# -*- coding: utf-8 -*-
# Copyright <YEAR(S)> <AUTHOR(S)>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp.tests import common
from ..hooks import uninstall_hook


class TestDeliveryMultiDestination(common.SavepointCase):
    @classmethod
    def setUpClass(cls):
        super(TestDeliveryMultiDestination, cls).setUpClass()
        cls.country_1 = cls.env['res.country'].create({
            'name': 'Test country 1',
        })
        cls.country_2 = cls.env['res.country'].create({
            'name': 'Test country 2',
        })
        cls.partner_1 = cls.env['res.partner'].create({
            'name': 'Test partner 1',
            'country_id': cls.country_1.id,
        })
        cls.partner_2 = cls.env['res.partner'].create({
            'name': 'Test partner 2',
            'country_id': cls.country_2.id,
        })
        cls.carrier_multi = cls.env['delivery.carrier'].create({
            'name': 'Test carrier multi',
            'partner_id': cls.partner_1.id,
            'destination_type': 'multi',
            'delivery_type': 'fixed',
            'fixed_price': 100,
            'child_ids': [
                (0, 0, {
                    'sequence': 1,
                    'partner_id': cls.partner_1.id,
                    'country_ids': [(6, 0, cls.country_1.ids)],
                    'delivery_type': 'fixed',
                    'fixed_price': 50,
                }),
                (0, 0, {
                    'sequence': 2,
                    'partner_id': cls.partner_1.id,
                    'country_ids': [(6, 0, cls.country_2.ids)],
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
            'order_line': [
                (0, 0, {
                    'name': 'Test',
                    'product_id': cls.product.id,
                    'product_uom_qty': 1,
                }),
            ]
        })

    def test_delivery_multi_destination(self):
        order = self.sale_order.with_context(test_delivery_multi=True)
        order.carrier_id = self.carrier_single.id
        self.assertAlmostEqual(order.delivery_price, 100, 2)
        order.carrier_id = self.carrier_multi.id
        self.assertAlmostEqual(order.delivery_price, 50, 2)
        # HACK: Needed as Odoo doesn't recompute non stored fields in tests
        order.invalidate_cache()
        order.partner_shipping_id = self.partner_2.id
        order.partner_id = self.partner_2.id
        self.assertAlmostEqual(order.delivery_price, 150, 2)

    def test_uninstall_hook(self):
        uninstall_hook(self.env.cr, self.env.registry)
        act_window = self.env.ref('delivery.action_delivery_carrier_form')
        self.assertFalse(act_window.domain)
