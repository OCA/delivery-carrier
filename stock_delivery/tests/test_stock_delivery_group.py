# -*- coding: utf-8 -*-
# © 2016-TODAY LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp.tests.common import TransactionCase


class TestStockDeliveryGroup(TransactionCase):

    def setUp(self, *args, **kwargs):
        super(TestStockDeliveryGroup, self).setUp(*args, **kwargs)

    def new_record(self):
        self.picking_id = self.env['stock.picking'].create({
            'location_dest_id': self.env['stock.location'].search([])[0].id,
            'location_id': self.env['stock.location'].search([])[0].id,
            'picking_type_id':
                self.env['stock.picking.type'].search([])[0].id,
        })
        self.inch_id = self.env.ref('product.product_uom_inch')
        self.oz_id = self.env.ref('product.product_uom_oz')
        self.pack_vals = {
            'length': 1.0,
            'height': 2.0,
            'width': 3.0,
            'length_uom_id': self.inch_id.id,
            'height_uom_id': self.inch_id.id,
            'width_uom_id': self.inch_id.id,
            'weight_uom_id': self.oz_id.id,
            'weight': 4.0,
            'name': 'TestPack',
        }
        self.pack_tpl_id = self.env['stock.delivery.pack.template'].create(
            self.pack_vals,
        )
        quant_pack_id = self.env['stock.quant.package'].create({})
        pack_vals = {'pack_template_id': self.pack_tpl_id.id,
                     'quant_pack_id': quant_pack_id.id,
                     }
        pack_vals.update(self.pack_vals)
        self.pack_id = self.env['stock.delivery.pack'].create(pack_vals)
        return self.env['stock.delivery.group'].create({
            'picking_id': self.picking_id.id,
            'pack_id': self.pack_id.id,
        })

    def new_operation(self, group_id):
        return self.env['stock.delivery.operation'].create({
            'group_id': group_id.id,
        })

    def test_last_operation_id(self):
        rec_id = self.new_record()
        self.new_operation(rec_id)
        op_id = self.new_operation(rec_id)
        self.assertEqual(
            op_id, rec_id.last_operation_id,
            'Did not get proper last op. Expect %s, Got %s' % (
                op_id, rec_id.last_operation_id,
            )
        )
