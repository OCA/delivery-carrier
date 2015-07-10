# -*- coding: utf-8 -*-
#
#
#    Authors: Guewen Baconnier
#    Copyright 2015 Camptocamp SA
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
#

import mock
from openerp.tests import common
from openerp.addons.delivery_carrier_label_postlogistics\
    .postlogistics.web_service import PostlogisticsWebService


class FakeWS(PostlogisticsWebService):
    def generate_label(self, picking, packages, user_lang=None):
        # call super to pass in the methods so we can check their
        # behavior.
        super(FakeWS, self).generate_label(picking, packages,
                                           user_lang=user_lang)
        # but returns a fake label
        result = {
            'value': [{'item_id': picking.id,
                       'binary': '',
                       'tracking_number': 'XYZ',
                       'file_type': 'pdf',
                       }],
        }
        return result


client_path = ('openerp.addons.delivery_carrier_label_postlogistics'
               '.postlogistics.web_service.Client')
auth_path = ('openerp.addons.delivery_carrier_label_postlogistics'
             '.postlogistics.web_service.HttpAuthenticated')
output_path = ('openerp.addons.delivery_carrier_label_postlogistics'
               '.postlogistics.web_service.PostlogisticsWebService'
               '._get_output_format')


class TestPostlogistics(common.TransactionCase):

    def setUp(self):
        super(TestPostlogistics, self).setUp()
        Product = self.env['product.product']
        partner_xmlid = 'delivery_carrier_label_postlogistics.postlogistics'
        self.carrier = self.env['delivery.carrier'].create({
            'name': 'Postlogistics',
            'type': 'postlogistics',
            'product_id': Product.create({'name': 'Shipping'}).id,
            'partner_id': self.env.ref(partner_xmlid).id,
        })
        Picking = self.env['stock.picking']
        self.picking = Picking.create({
            'carrier_id': self.carrier.id,
            'picking_type_id': self.env.ref('stock.picking_type_out').id,
        })
        product = Product.create({'name': 'Product A'})

        stock_location = self.env.ref('stock.stock_location_stock')
        customer_location = self.env.ref('stock.stock_location_customers')
        self.env['stock.move'].create({
            'name': 'a move',
            'product_id': product.id,
            'product_uom_qty': 3.0,
            'product_uom': product.uom_id.id,
            'picking_id': self.picking.id,
            'location_id': stock_location.id,
            'location_dest_id': customer_location.id,
        })
        self.env.user.lang = 'en_US'

    def test_store_label(self):
        with mock.patch(client_path), mock.patch(auth_path),\
                mock.patch(output_path):
            res = self.picking._generate_postlogistics_label(
                webservice_class=FakeWS
            )
            expected = [{'file': '',
                         'file_type': 'pdf',
                         'name': 'XYZ.pdf',
                         'package_id': False}]
            self.assertEqual(res, expected)
            self.assertEqual(self.picking.carrier_tracking_ref, 'XYZ')

    def test_missing_language(self):
        self.env.user.lang = False
        with mock.patch(client_path), mock.patch(auth_path),\
                mock.patch(output_path):
            self.picking._generate_postlogistics_label(webservice_class=FakeWS)
