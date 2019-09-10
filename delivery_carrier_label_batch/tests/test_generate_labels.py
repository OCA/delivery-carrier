# Copyright 2013-2019 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
import base64

import odoo.tests.common as common
from odoo.modules import get_module_resource


class TestGenerateLabels(common.TransactionCase):

    """ Test the wizard for delivery carrier label generation """

    def setUp(self):
        super(TestGenerateLabels, self).setUp()

        Move = self.env['stock.move']
        Picking = self.env['stock.picking']
        ShippingLabel = self.env['shipping.label']
        BatchPicking = self.env['stock.batch.picking']
        self.DeliveryCarrierLabelGenerate = self.env[
            'delivery.carrier.label.generate']

        self.batch = BatchPicking.create(
            {'name': 'demo_prep001',
             'picker_id': self.ref('base.user_demo'),
             })

        picking_out_1 = Picking.create(
            {'partner_id': self.ref('base.res_partner_12'),
             'batch_picking_id': self.batch.id,
             'location_id': self.ref('stock.stock_location_14'),
             'location_dest_id': self.ref('stock.stock_location_7'),
             'picking_type_id': self.ref('stock.picking_type_out')})

        picking_out_2 = Picking.create(
            {'partner_id': self.ref('base.res_partner_12'),
             'batch_picking_id': self.batch.id,
             'location_id': self.ref('stock.stock_location_14'),
             'location_dest_id': self.ref('stock.stock_location_7'),
             'picking_type_id': self.ref('stock.picking_type_out')})

        Move.create(
            {'name': '/',
             'picking_id': picking_out_1.id,
             'product_id': self.ref('product.product_delivery_01'),
             'product_uom': self.ref('uom.product_uom_unit'),
             'product_uom_qty': 2,
             'location_id': self.ref('stock.stock_location_14'),
             'location_dest_id': self.ref('stock.stock_location_7'),
             })

        Move.create(
            {'name': '/',
             'picking_id': picking_out_2.id,
             'product_id': self.ref('product.product_delivery_01'),
             'product_uom': self.ref('uom.product_uom_unit'),
             'product_uom_qty': 1,
             'location_id': self.ref('stock.stock_location_14'),
             'location_dest_id': self.ref('stock.stock_location_7'),
             })

        label = ''
        dummy_pdf_path = get_module_resource('delivery_carrier_label_batch',
                                             'tests', 'dummy.pdf')
        with open(dummy_pdf_path, 'rb') as dummy_pdf:
            label = dummy_pdf.read()

        ShippingLabel.create(
            {'name': 'picking_out_1',
             'res_id': picking_out_1.id,
             'res_model': 'stock.picking',
             'datas': base64.b64encode(label),
             'file_type': 'pdf',
             })

        ShippingLabel.create(
            {'name': 'picking_out_2',
             'res_id': picking_out_2.id,
             'res_model': 'stock.picking',
             'datas': base64.b64encode(label),
             'file_type': 'pdf',
             })

    def test_00_action_generate_labels(self):
        """ Check merging of pdf labels

        We don't test pdf generation as without dependancies the
        test would fail

        """
        wizard = self.DeliveryCarrierLabelGenerate.with_context(
            active_ids=self.batch.ids,
            active_model='stock.batch.picking').create({})
        wizard.action_generate_labels()

        attachment = self.env['ir.attachment'].search(
            [('res_model', '=', 'stock.batch.picking'),
             ('res_id', '=', self.batch.id)]
        )

        self.assertEqual(len(attachment), 1)
        self.assertTrue(attachment.datas)
        self.assertTrue(attachment.name, 'demo_prep001.pdf')
        self.assertTrue(attachment.mimetype, 'application/pdf')
