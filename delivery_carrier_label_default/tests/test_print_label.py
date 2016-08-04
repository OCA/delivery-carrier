# -*- coding: utf-8 -*-
# Copyright 2016 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
from openerp.tests import common


class TestPrintLabel(common.TransactionCase):

    def test_print_default_label(self):
        self.picking.generate_labels()
        label = self.env['shipping.label'].search(
            [('res_id', '=', self.picking.id)])
        self.assertEquals(len(label), 1)
        self.assertTrue(label.datas)
        self.assertEquals(label.name, "Shipping Label.pdf")
        self.assertEquals(label.file_type, 'pdf')

    def test_print_default_label_multi_packs(self):
        # create packs
        self.picking.action_confirm()
        self.picking.force_assign()
        self.picking.pack_operation_product_ids[0].qty_done = 3
        self.picking.pack_operation_product_ids[1].qty_done = 3
        self.picking.put_in_pack()
        for ope in self.picking.pack_operation_product_ids:
            if ope.qty_done == 0:
                ope.qty_done = 9
                break
        self.picking.put_in_pack()
        self.picking.generate_labels()
        label = self.env['shipping.label'].search(
            [('res_id', '=', self.picking.id)])
        self.assertEquals(len(label), 1)
        self.assertTrue(label[0].datas)
        self.assertEquals(label[0].name, "Shipping Label.pdf")
        self.assertEquals(label[0].file_type, 'pdf')

    def test_print_default_label_selected_packs(self):
        # create packs
        self.picking.action_confirm()
        self.picking.force_assign()
        self.picking.pack_operation_product_ids[0].qty_done = 3
        self.picking.pack_operation_product_ids[1].qty_done = 3
        self.picking.put_in_pack()
        for ope in self.picking.pack_operation_product_ids:
            if ope.qty_done == 0:
                ope.qty_done = 9
                break
        self.picking.put_in_pack()
        packs = self.picking.mapped(
            'pack_operation_product_ids.result_package_id')
        self.picking.generate_labels(package_ids=packs.ids)
        labels = self.env['shipping.label'].search(
            [('res_id', '=', self.picking.id)])
        self.assertEquals(len(labels), 2)
        self.assertTrue(labels[0].datas)
        self.assertEquals(labels[0].name, "Shipping Label.pdf")
        self.assertEquals(labels[0].file_type, 'pdf')

    def setUp(self):
        super(TestPrintLabel, self).setUp()
        Product = self.env['product.product']
        stock_location = self.env.ref('stock.stock_location_stock')
        customer_location = self.env.ref('stock.stock_location_customers')
        Picking = self.env['stock.picking']
        self.picking = Picking.create({
            'picking_type_id': self.env.ref('stock.picking_type_out').id,
            'location_id': stock_location.id,
            'location_dest_id': customer_location.id,
        })
        product_a = Product.create({'name': 'Product A'})
        product_b = Product.create({'name': 'Product B'})

        self.env['stock.move'].create({
            'name': 'a move',
            'product_id': product_a.id,
            'product_uom_qty': 3.0,
            'product_uom': product_a.uom_id.id,
            'picking_id': self.picking.id,
            'location_id': stock_location.id,
            'location_dest_id': customer_location.id,
        })
        self.env['stock.move'].create({
            'name': 'a second move',
            'product_id': product_b.id,
            'product_uom_qty': 12.0,
            'product_uom': product_b.uom_id.id,
            'picking_id': self.picking.id,
            'location_id': stock_location.id,
            'location_dest_id': customer_location.id,
        })
