# Copyright 2019 Tecnativa - Victor M.M. Torres
# Copyright 2019-2020 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.addons.sale.tests.test_sale_common import TestSale


class TestStockPickingInfoComputation(TestSale):
    def setUp(self):
        super(TestStockPickingInfoComputation, self).setUp()
        self.product_category_5 = self.env.ref('product.product_category_5')
        self.product_pricelist_0 = self.env.ref('product.list0')
        self.product_a = self.env['product.product'].create({
            'name': 'Test product A',
            'type': 'product',
            'weight': 0.3,
            'volume': 0.02,
        })
        self.product_b = self.env['product.product'].create({
            'name': 'Test product B',
            'type': 'consu',
            'weight': 0.25,
            'volume': 0.03,
        })
        self.sale_test = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'partner_invoice_id': self.partner.id,
            'partner_shipping_id': self.partner.id,
            'pricelist_id': self.product_pricelist_0.id,
            'order_line': [
                (0, 0, {
                    'name': self.product_a.name,
                    'product_id': self.product_a.id,
                    'product_uom_qty': 2,
                    'product_uom': self.product_a.uom_id.id,
                    'price_unit': 300.00,
                }),
                (0, 0, {
                    'name': self.product_b.name,
                    'product_id': self.product_b.id,
                    'product_uom_qty': 5,
                    'product_uom': self.product_b.uom_id.id,
                    'price_unit': 390.00,
                })
            ],
            'picking_policy': 'direct',
        })

    def test_weight_volume_with_done_qty(self):
        self.sale_test.action_confirm()
        picking = self.sale_test.picking_ids
        self.assertAlmostEqual(picking.weight, 1.25)  # Prod. B - 0.25 * 5
        self.assertAlmostEqual(picking.volume, 0.15)  # Prod. B - 0.03 * 5
        move = picking.move_ids_without_package.filtered(
            lambda x: x.product_id == self.product_a
        )
        # Needed for creating backorder
        move.write({'quantity_done': 1})
        self.assertAlmostEqual(picking.weight, 0.3)  # Prod. A - 0.3 * 1
        picking.action_calculate_volume()
        self.assertAlmostEqual(picking.volume, 0.02)  # Prod. A - 0.02 * 1
        # Confirm and create backorder
        picking.action_done()
        backorder = self.sale_test.picking_ids - picking
        self.assertAlmostEqual(backorder.weight, 1.25)  # Prod. B - 0.25 * 5
        self.assertAlmostEqual(backorder.volume, 0.15)  # Prod. B - 0.03 * 5
        backorder.do_unreserve()
        backorder.action_calculate_volume()
        self.assertAlmostEqual(backorder.weight, 1.55)  # 0.3 * 1 + 0.25 * 5
        self.assertAlmostEqual(backorder.volume, 0.17)  # 0.02 * 1 + 0.03 * 5

    def test_weight_volume_with_reserved_qty(self):
        # Add stock quantity
        self.env['stock.quant'].create({
            'product_id': self.product_a.id,
            'location_id': self.sale_test.warehouse_id.lot_stock_id.id,
            'quantity': 1,
        })
        self.sale_test.action_confirm()
        picking = self.sale_test.picking_ids
        picking.action_assign()
        self.assertAlmostEqual(picking.weight, 1.55)  # 0.3 * 1 + 0.25 * 5
        picking.action_calculate_volume()
        self.assertAlmostEqual(picking.volume, 0.17)  # 0.02 * 1 + 0.03 * 5
