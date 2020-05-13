# Copyright 2018 Tecnativa - Sergio Teruel
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.tests import SavepointCase
from odoo.tests.common import Form
from lxml import etree


class TestPartnerDeliveryZone(SavepointCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.warehouse = cls.env.ref('stock.warehouse0')
        cls.delivery_zone_a = cls.env['partner.delivery.zone'].create({
            'name': 'Delivery Zone A',
            'code': '10',
        })
        cls.delivery_zone_b = cls.env['partner.delivery.zone'].create({
            'name': 'Delivery Zone A',
            'code': '10',
        })
        cls.partner = cls.env['res.partner'].create({
            'name': 'test',
            'delivery_zone_id': cls.delivery_zone_a.id
        })
        cls.product = cls.env['product.product'].create({
            'name': 'test',
        })
        order_form = Form(cls.env['sale.order'])
        order_form.partner_id = cls.partner
        with order_form.order_line.new() as line_form:
            line_form.product_id = cls.product
            line_form.price_unit = 1000
        cls.order = order_form.save()
        cls.View = cls.env['ir.ui.view']

    def test_partner_child_propagate(self):
        other_partner = self.env['res.partner'].create({
            'name': 'other partner',
            'delivery_zone_id': self.delivery_zone_b.id,
        })
        self.order.partner_shipping_id = other_partner
        self.order.onchange_partner_shipping_id_delivery_zone()
        self.assertEqual(
            self.order.delivery_zone_id, other_partner.delivery_zone_id)

    def test_sale_order_confirm(self):
        self.order.action_confirm()
        self.assertEqual(
            self.order.picking_ids.delivery_zone_id,
            self.partner.delivery_zone_id)

    def test_stock_picking(self):
        partner2 = self.env['res.partner'].create({
            'name': 'partner 2',
            'delivery_zone_id': self.delivery_zone_b.id,
        })
        self.order.action_confirm()
        self.order.picking_ids.partner_id = partner2
        self.order.picking_ids.onchange_partner_id_zone()
        self.assertEqual(
            self.order.picking_ids.delivery_zone_id,
            self.delivery_zone_b)

    def _get_ctx_from_view(self, res):
        partner_xml = etree.XML(res['arch'])
        partner_path = "//field[@name='child_ids']"
        partner_field = partner_xml.xpath(partner_path)[0]
        return partner_field.attrib.get("context", "{}")

    def test_default_line_discount_value(self):
        res = self.partner.fields_view_get(
            view_id=self.env.ref('partner_delivery_zone.view_partner_form').id,
            view_type='form')
        ctx = self._get_ctx_from_view(res)
        self.assertTrue('default_delivery_zone_id' in ctx)
        view = self.View.create({
            'name': "test",
            'type': "form",
            'model': 'res.partner',
            'arch': """
                <data>
                    <field name='child_ids'
                        context="{'default_name': 'test'}">
                    </field>
                </data>
            """
        })
        res = self.partner.fields_view_get(view_id=view.id, view_type='form')
        ctx = self._get_ctx_from_view(res)
        self.assertTrue('default_delivery_zone_id' in ctx)

    def test_wharehouse_three_steps(self):
        self.warehouse.delivery_steps = 'pick_pack_ship'
        self.order.action_confirm()
        for picking in self.order.picking_ids:
            self.assertEqual(
                picking.delivery_zone_id, self.order.delivery_zone_id)

    def test_wharehouse_three_steps_so_wo_delivery_zone(self):
        # If SO has not delivery zone, all pickings obtains the delivery zone
        # from shipping partner
        self.warehouse.delivery_steps = 'pick_pack_ship'
        self.order.delivery_zone_id = False
        self.order.action_confirm()
        for picking in self.order.picking_ids:
            self.assertEqual(
                picking.delivery_zone_id,
                self.order.partner_shipping_id.delivery_zone_id
            )
