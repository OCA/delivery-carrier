# Copyright 2013-2019 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
import mock
import base64

from odoo.tests import common

from .common import HTMLRenderMixin

MOD_PATH = 'odoo.addons.base_delivery_carrier_label.models'
LABEL_MODEL = MOD_PATH + '.shipping_label.ShippingLabel'


def patch_label_file_type(function):
    """Decorator to patch the 'shipping.label.file_type' selection field
    to allow the 'html' type when running tests.
    """
    def wrapper(*args, **kwargs):
        with mock.patch(LABEL_MODEL + '._selection_file_type') as (
                _selection_file_type):
            _selection_file_type.return_value = [('html', 'HTML')]
            result = function(*args, **kwargs)
        return result
    return wrapper


class TestPrintLabel(common.SavepointCase, HTMLRenderMixin):
    """Test label printing.

    When running tests Odoo renders PDF reports as HTML,
    so we are going to test the shipping labels as HTML document only.
    A good side effect: we are able to test the rendered content.
    """
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        Product = cls.env['product.product']
        stock_location = cls.env.ref('stock.stock_location_stock')
        customer_location = cls.env.ref('stock.stock_location_customers')
        Picking = cls.env['stock.picking']
        cls.picking = Picking.create({
            'picking_type_id': cls.env.ref('stock.picking_type_out').id,
            'location_id': stock_location.id,
            'location_dest_id': customer_location.id,
        })
        product_a = Product.create({'name': 'Product A'})
        product_b = Product.create({'name': 'Product B'})

        cls.env['stock.move'].create({
            'name': 'a move',
            'product_id': product_a.id,
            'product_uom_qty': 3.0,
            'product_uom': product_a.uom_id.id,
            'picking_id': cls.picking.id,
            'location_id': stock_location.id,
            'location_dest_id': customer_location.id,
        })
        cls.env['stock.move'].create({
            'name': 'a second move',
            'product_id': product_b.id,
            'product_uom_qty': 12.0,
            'product_uom': product_b.uom_id.id,
            'picking_id': cls.picking.id,
            'location_id': stock_location.id,
            'location_dest_id': customer_location.id,
        })

    def check_label_content(self, b64_datas):
        html_datas = base64.b64decode(b64_datas)
        node = self.to_xml_node(html_datas)[0]
        for div_class in ['page', 'address', 'recipient']:
            tags = self.find_div_class(node, div_class)
            self.assertEqual(len(tags), 1)

    @patch_label_file_type
    def test_print_default_label(self):
        # assign picking to generate 'stock.move.line'
        self.picking.action_confirm()
        self.picking.action_assign()
        self.picking.action_generate_carrier_label()
        label = self.env['shipping.label'].search(
            [('res_id', '=', self.picking.id)])
        self.assertEquals(len(label), 1)
        self.assertTrue(label.datas)
        self.assertEquals(label.name, "Shipping Label.html")
        self.assertEquals(label.file_type, 'html')
        self.check_label_content(label.datas)

    @patch_label_file_type
    def test_print_default_label_selected_packs(self):
        # create packs
        self.picking.action_confirm()
        self.picking.action_assign()
        self.picking.move_line_ids[0].qty_done = 3
        self.picking.move_line_ids[1].qty_done = 3
        self.picking.put_in_pack()
        for ope in self.picking.move_line_ids:
            if ope.qty_done == 0:
                ope.qty_done = 9
                break
        self.picking.put_in_pack()
        self.picking.action_generate_carrier_label()
        labels = self.env['shipping.label'].search(
            [('res_id', '=', self.picking.id)])
        self.assertEquals(len(labels), 2)
        for label in labels:
            self.assertTrue(label.datas)
            self.assertEquals(label.name, "Shipping Label.html")
            self.assertEquals(label.file_type, 'html')
            self.check_label_content(label.datas)
