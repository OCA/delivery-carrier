# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Yannick Vaucher
#    Copyright 2013 Camptocamp SA
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
import openerp.tests.common as common
from openerp.addons import get_module_resource


class test_generate_labels(common.TransactionCase):

    """ Test the wizard for delivery carrier label generation """

    def setUp(self):
        super(test_generate_labels, self).setUp()
        cr, uid = self.cr, self.uid

        self.Move = self.registry('stock.move')
        self.Picking = self.registry('stock.picking')
        self.ShippingLabel = self.registry('shipping.label')
        self.PickingDispatch = self.registry('picking.dispatch')
        self.DeliveryCarrierLabelGenerate = self.registry(
            'delivery.carrier.label.generate')

        picking_out_1_id = self.Picking.create(
            cr, uid,
            {'partner_id': self.ref('base.res_partner_12'),
             'type': 'out'})

        picking_out_2_id = self.Picking.create(
            cr, uid,
            {'partner_id': self.ref('base.res_partner_12'),
             'type': 'out'})

        self.picking_dispatch_id = self.PickingDispatch.create(
            cr, uid,
            {'name': 'demo_prep001',
             'picker_id': self.ref('base.user_demo'),
             })

        self.Move.create(
            cr, uid,
            {'name': '/',
             'picking_id': picking_out_1_id,
             'dispatch_id': self.picking_dispatch_id,
             'product_id': self.ref('product.product_product_33'),
             'product_uom': self.ref('product.product_uom_unit'),
             'product_qty': 2,
             'location_id': self.ref('stock.stock_location_14'),
             'location_dest_id': self.ref('stock.stock_location_7'),
             })

        self.Move.create(
            cr, uid,
            {'name': '/',
             'picking_id': picking_out_2_id,
             'dispatch_id': self.picking_dispatch_id,
             'product_id': self.ref('product.product_product_33'),
             'product_uom': self.ref('product.product_uom_unit'),
             'product_qty': 1,
             'location_id': self.ref('stock.stock_location_14'),
             'location_dest_id': self.ref('stock.stock_location_7'),
             })

        label = ''
        dummy_pdf_path = get_module_resource('delivery_carrier_label_dispatch',
                                             'tests', 'dummy.pdf')
        with file(dummy_pdf_path) as dummy_pdf:
            label = dummy_pdf.read()

        self.ShippingLabel.create(
            cr, uid,
            {'name': 'picking_out_1',
             'res_id': picking_out_1_id,
             'res_model': 'stock.picking.out',
             'datas': label.encode('base64'),
             'file_type': 'pdf',
             })

        self.ShippingLabel.create(
            cr, uid,
            {'name': 'picking_out_2',
             'res_id': picking_out_2_id,
             'res_model': 'stock.picking.out',
             'datas': label.encode('base64'),
             'file_type': 'pdf',
             })

    def test_00_action_generate_labels(self):
        """ Check merging of pdf labels

        We don't test pdf generation as without dependancies the
        test would fail

        """
        cr, uid = self.cr, self.uid
        active_ids = [self.picking_dispatch_id]
        wizard_id = self.DeliveryCarrierLabelGenerate.create(
            cr, uid,
            {},
            context={'active_ids': active_ids,
                     'active_model': 'picking.dispatch'})
        wizard = self.DeliveryCarrierLabelGenerate.browse(
            cr, uid, [wizard_id], context=None)
        self.DeliveryCarrierLabelGenerate.action_generate_labels(
            cr, uid, [wizard_id], context={'active_ids': active_ids})
        wizard = self.DeliveryCarrierLabelGenerate.browse(
            cr, uid, wizard_id, context=None)
        assert wizard.label_pdf_file
