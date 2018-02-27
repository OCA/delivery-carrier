# -*- coding: utf-8 -*-
# Copyright 2018 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests import common


def _execute_onchanges(records, field_name):
    """Helper methods that executes all onchanges associated to a field."""
    for onchange in records._onchange_methods.get(field_name, []):
        for record in records:
            onchange(record)


@common.at_install(False)
@common.post_install(True)
class TestDeliveryAutoRefresh(common.HttpCase):
    def setUp(self):
        super(TestDeliveryAutoRefresh, self).setUp()
        self.carrier = self.env['delivery.carrier'].create({
            'name': 'Test carrier',
            'delivery_type': 'base_on_rule',
            'price_rule_ids': [
                (0, 0, {
                    'variable': 'weight',
                    'operator': '<=',
                    'max_value': 20,
                    'list_base_price': 50,
                }),
                (0, 0, {
                    'variable': 'weight',
                    'operator': '<=',
                    'max_value': 40,
                    'list_base_price': 30,
                    'list_price': 1,
                    'variable_factor': 'weight',
                }),
                (0, 0, {
                    'variable': 'weight',
                    'operator': '>',
                    'max_value': 40,
                    'list_base_price': 20,
                    'list_price': 1.5,
                    'variable_factor': 'weight',
                }),
            ]
        })
        self.product = self.env['product.product'].create({
            'name': 'Test product',
            'weight': 10,
            'list_price': 20,
        })
        self.partner = self.env['res.partner'].create({
            'name': 'Test partner',
            'property_delivery_carrier_id': self.carrier.id,
        })
        self.param_name = 'delivery_auto_refresh.auto_add_delivery_line'
        order = self.env['sale.order'].new({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'product_uom_qty': 2,
                })
            ]
        })
        _execute_onchanges(order, 'partner_id')
        _execute_onchanges(order.order_line, 'product_id')
        self.order = order.create(order._convert_to_write(order._cache))

    def test_auto_refresh_so(self):
        self.assertFalse(self.order.order_line.filtered('is_delivery'))
        self.env['ir.config_parameter'].sudo().set_param(self.param_name, 1)
        order2 = self.order.copy({})
        self.assertTrue(order2.order_line.filtered('is_delivery'))
        self.order.write({
            'order_line': [
                (1, self.order.order_line.id, {'product_uom_qty': 3}),
            ],
        })
        line_delivery = self.order.order_line.filtered('is_delivery')
        self.assertEqual(line_delivery.price_unit, 60)
        line2 = self.order.order_line.new({
            'order_id': self.order.id,
            'product_id': self.product.id,
            'product_uom_qty': 2,
        })
        _execute_onchanges(line2, 'product_id')
        vals = line2._convert_to_write(line2._cache)
        del vals['order_id']
        self.order.write({'order_line': [(0, 0, vals)]})
        line_delivery = self.order.order_line.filtered('is_delivery')
        self.assertEqual(line_delivery.price_unit, 95)

    def test_auto_refresh_picking(self):
        self.order.order_line.product_uom_qty = 3
        self.order.action_confirm()
        picking = self.order.picking_ids
        picking.force_assign()
        picking.pack_operation_ids[0].qty_done = 2
        picking.do_transfer()
        line_delivery = self.order.order_line.filtered('is_delivery')
        self.assertEqual(line_delivery.price_unit, 50)
