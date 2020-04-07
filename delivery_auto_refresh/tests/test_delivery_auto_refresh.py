# Copyright 2018 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests import common


def _execute_onchanges(records, field_name):
    """Helper methods that executes all onchanges associated to a field."""
    for onchange in records._onchange_methods.get(field_name, []):
        for record in records:
            onchange(record)


class TestDeliveryAutoRefresh(common.HttpCase):
    def setUp(self):
        super(TestDeliveryAutoRefresh, self).setUp()
        service = self.env['product.product'].create({
            'name': 'Service Test',
            'type': 'service',
        })
        service_fixed = self.env['product.product'].create({
            'name': 'Service Test Fixed',
            'type': 'service',
        })
        self.carrier = self.env['delivery.carrier'].create({
            'name': 'Test carrier',
            'delivery_type': 'base_on_rule',
            'product_id': service.id,
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
        self.carrier_fixed = self.env['delivery.carrier'].create({
            'name': 'Test carrier fixed',
            'delivery_type': 'fixed',
            'product_id': service_fixed.id,
            'fixed_price': 10.0,
        })
        self.product = self.env['product.product'].create({
            'name': 'Test product',
            'weight': 10,
            'list_price': 20,
        })
        self.product_fixed = self.env['product.product'].create({
            'name': 'Test product fixed',
            'weight': 10,
            'list_price': 20,
        })
        self.partner = self.env['res.partner'].create({
            'name': 'Test partner',
            'property_delivery_carrier_id': self.carrier.id,
        })
        self.partner_fixed = self.env['res.partner'].create({
            'name': 'Test partner fixed delivery',
            'property_delivery_carrier_id': self.carrier_fixed.id,
        })
        self.param_name1 = 'delivery_auto_refresh.auto_add_delivery_line'
        self.param_name2 = 'delivery_auto_refresh.refresh_after_picking'
        order = self.env['sale.order'].new({
            'partner_id': self.partner.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product.id,
                    'product_uom_qty': 2,
                })
            ]
        })
        order_fixed = self.env['sale.order'].new({
            'partner_id': self.partner_fixed.id,
            'order_line': [
                (0, 0, {
                    'product_id': self.product_fixed.id,
                    'product_uom_qty': 2,
                })
            ]
        })
        _execute_onchanges(order, 'partner_id')
        _execute_onchanges(order.order_line, 'product_id')
        self.order = order.create(order._convert_to_write(order._cache))
        _execute_onchanges(order_fixed, 'partner_id')
        _execute_onchanges(order_fixed.order_line, 'product_id')
        self.order_fixed = order_fixed.create(
            order_fixed._convert_to_write(order_fixed._cache)
        )

    def test_auto_refresh_so(self):
        self.assertFalse(self.order.order_line.filtered('is_delivery'))
        self.env['ir.config_parameter'].sudo().set_param(self.param_name1, 1)
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
        self.env['ir.config_parameter'].sudo().set_param(self.param_name2, 1)
        self.order.order_line.product_uom_qty = 3
        self.order.action_confirm()
        picking = self.order.picking_ids
        picking.action_assign()
        picking.move_line_ids[0].qty_done = 2
        picking.action_done()
        line_delivery = self.order.order_line.filtered('is_delivery')
        self.assertEqual(line_delivery.price_unit, 50)

    def test_no_auto_refresh_picking(self):
        self.env['ir.config_parameter'].sudo().set_param(self.param_name2, "0")
        self.order.order_line.product_uom_qty = 3
        self.order.action_confirm()
        picking = self.order.picking_ids
        picking.action_assign()
        picking.move_line_ids[0].qty_done = 2
        picking.action_done()
        line_delivery = self.order.order_line.filtered('is_delivery')
        self.assertEqual(line_delivery.price_unit, 60)

    def test_auto_refresh_so_fixed(self):
        self.assertFalse(self.order_fixed.order_line.filtered('is_delivery'))
        self.env['ir.config_parameter'].sudo().set_param(self.param_name1, 1)
        self.order_fixed.write({
            'order_line': [
                (1, self.order_fixed.order_line.id, {'product_uom_qty': 3}),
            ],
        })
        line_delivery = self.order_fixed.order_line.filtered('is_delivery')
        self.assertEqual(line_delivery.price_unit, 10)
        line2 = self.order_fixed.order_line.new({
            'order_id': self.order_fixed.id,
            'product_id': self.product_fixed.id,
            'product_uom_qty': 2,
        })
        _execute_onchanges(line2, 'product_id')
        vals = line2._convert_to_write(line2._cache)
        del vals['order_id']
        self.order_fixed.write({'order_line': [(0, 0, vals)]})
        line_delivery = self.order_fixed.order_line.filtered('is_delivery')
        self.assertEqual(line_delivery.price_unit, 10)

    def test_auto_refresh_picking_fixed(self):
        self.env['ir.config_parameter'].sudo().set_param(self.param_name2, 1)
        self.order_fixed.order_line.create({
            'order_id': self.order_fixed.id,
            'product_id': self.product_fixed.id,
            'product_uom_qty': 2,
        })
        self.order_fixed.order_line.product_uom_qty = 3
        self.order_fixed.action_confirm()
        picking = self.order_fixed.picking_ids
        picking.action_assign()
        picking.move_line_ids[0].qty_done = 2
        picking.action_done()
        line_delivery = self.order_fixed.order_line.filtered('is_delivery')
        self.assertEqual(line_delivery.price_unit, 10)

    def test_no_auto_refresh_picking_fixed(self):
        self.env['ir.config_parameter'].sudo().set_param(self.param_name2, "0")
        self.order_fixed.order_line.create({
            'order_id': self.order_fixed.id,
            'product_id': self.product_fixed.id,
            'product_uom_qty': 2,
        })
        self.order_fixed.order_line.product_uom_qty = 3
        self.order_fixed.action_confirm()
        picking = self.order_fixed.picking_ids
        picking.action_assign()
        picking.move_line_ids[0].qty_done = 2
        picking.action_done()
        line_delivery = self.order_fixed.order_line.filtered('is_delivery')
        self.assertEqual(line_delivery.price_unit, 10)
