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
        BatchPicking = self.env['stock.picking.batch']
        self.DeliveryCarrierLabelGenerate = self.env[
            'delivery.carrier.label.generate']
        self.stock_location = self.env.ref('stock.stock_location_stock')
        self.customer_location = self.env.ref('stock.stock_location_customers')

        self.productA = self.env['product.product'].create({
            'name': 'Product A',
            'type': 'product'
        })
        self.productB = self.env['product.product'].create({
            'name': 'Product B',
            'type': 'product'
        })
        self.env['stock.quant']._update_available_quantity(
            self.productA,
            self.stock_location,
            20.0
        )
        self.env['stock.quant']._update_available_quantity(
            self.productB,
            self.stock_location,
            20.0
        )

        picking_out_1 = Picking.create(
            {'partner_id': self.ref('base.res_partner_12'),
             'location_id': self.stock_location.id,
             'location_dest_id': self.customer_location.id,
             'picking_type_id': self.ref('stock.picking_type_out')})

        picking_out_2 = Picking.create(
            {'partner_id': self.ref('base.res_partner_12'),
             'location_id': self.stock_location.id,
             'location_dest_id': self.customer_location.id,
             'picking_type_id': self.ref('stock.picking_type_out')})

        Move.create(
            {'name': '/',
             'picking_id': picking_out_1.id,
             'product_id': self.productA.id,
             'product_uom': self.ref('uom.product_uom_unit'),
             'product_uom_qty': 2,
             'location_id': self.stock_location.id,
             'location_dest_id': self.customer_location.id,
             })

        Move.create(
            {'name': '/',
             'picking_id': picking_out_2.id,
             'product_id': self.productB.id,
             'product_uom': self.ref('uom.product_uom_unit'),
             'product_uom_qty': 1,
             'location_id': self.stock_location.id,
             'location_dest_id': self.customer_location.id,
             })

        self.batch = BatchPicking.create(
            {'name': 'demo_prep001',
             'picking_ids': [(4, picking_out_1.id), (4, picking_out_2.id)],
             'use_oca_batch_validation': True
             })

        self.batch.confirm_picking()

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
            active_model='stock.picking.batch').create({})
        wizard.action_generate_labels()

        attachment = self.env['ir.attachment'].search(
            [('res_model', '=', 'stock.picking.batch'),
             ('res_id', '=', self.batch.id)]
        )

        self.assertEqual(len(attachment), 1)
        self.assertTrue(attachment.datas)
        self.assertTrue(attachment.name, 'demo_prep001.pdf')
        self.assertTrue(attachment.mimetype, 'application/pdf')
