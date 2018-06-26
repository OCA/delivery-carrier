# -*- coding: utf-8 -*-
# Copyright 2015-2017 Camptocamp
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import mock

from odoo.tests import common
from ..postlogistics.web_service import PostlogisticsWebService


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


client_path = ('odoo.addons.delivery_carrier_label_postlogistics'
               '.postlogistics.web_service.Client')
auth_path = ('odoo.addons.delivery_carrier_label_postlogistics'
             '.postlogistics.web_service.HttpAuthenticated')
output_path = ('odoo.addons.delivery_carrier_label_postlogistics'
               '.postlogistics.web_service.PostlogisticsWebService'
               '._get_output_format')


class TestPostlogistics(common.TransactionCase):

    def setUp(self):
        super(TestPostlogistics, self).setUp()
        Product = self.env['product.product']
        partner_xmlid = ('delivery_carrier_label_postlogistics'
                         '.partner_postlogistics')
        self.carrier = self.env['delivery.carrier'].create({
            'name': 'Postlogistics',
            'delivery_type': 'postlogistics',
            'product_id': Product.create({'name': 'Shipping'}).id,
            'partner_id': self.env.ref(partner_xmlid).id,
        })
        Option = self.env['delivery.carrier.template.option']
        label_layout = Option.create({'code': 'A6'})
        output_format = Option.create({'code': 'pdf'})
        image_resolution = Option.create({'code': '600pp'})
        self.env.user.company_id.write({
            'postlogistics_default_label_layout': label_layout.id,
            'postlogistics_default_output_format': output_format.id,
            'postlogistics_default_resolution': image_resolution.id,
        })
        stock_location = self.env.ref('stock.stock_location_stock')
        customer_location = self.env.ref('stock.stock_location_customers')
        Picking = self.env['stock.picking']
        self.picking = Picking.create({
            'carrier_id': self.carrier.id,
            'picking_type_id': self.env.ref('stock.picking_type_out').id,
            'location_id': stock_location.id,
            'location_dest_id': customer_location.id,
        })
        product = Product.create({'name': 'Product A'})

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
