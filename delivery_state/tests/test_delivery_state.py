# Copyright 2020 Trey, Kilobytes de Soluciones
# Copyright 2020 FactorLibre
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields
from odoo.tests.common import SavepointCase


class TestDeliveryState(SavepointCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        product_shipping_cost = cls.env['product.product'].create({
            'type': 'service',
            'name': 'Shipping costs',
            'standard_price': 10,
            'list_price': 100,
        })
        cls.carrier = cls.env['delivery.carrier'].create({
            'name': 'Test carrier',
            'delivery_type': 'fixed',
            'product_id': product_shipping_cost.id,
            'fixed_price': 99.99,
        })
        cls.product = cls.env["product.product"].create({
            "name": "Test product",
            "type": "product",
        })
        cls.partner = cls.env["res.partner"].create({
            "name": "Mr. Odoo",
            "email": "test@test.com",
        })
        cls.partner_shipping = cls.env["res.partner"].create({
            "name": "Mr. Odoo (Delivery Address)",
            "email": "test_shipping@test.com",
        })
        cls.pricelist = cls.env['product.pricelist'].create({
            'name': 'Test pricelist',
            'item_ids': [(0, 0, {
                'applied_on': '3_global',
                'compute_price': 'formula',
                'base': 'list_price',
            })]
        })
        cls.sale = cls.env['sale.order'].create({
            'partner_id': cls.partner.id,
            'partner_shipping_id': cls.partner_shipping.id,
            'carrier_id': cls.carrier.id,
            'pricelist_id': cls.pricelist.id,
            'order_line': [(0, 0, {
                'product_id': cls.product.id,
                'product_uom_qty': 1})]
        })

    def test_delivery_state(self):
        self.sale.get_delivery_price()
        self.assertEquals(self.sale.delivery_price, 99.99)
        self.sale.set_delivery_line()
        self.assertEquals(len(self.sale.order_line), 2)
        self.sale.action_confirm()
        picking = self.sale.picking_ids[0]
        self.assertEquals(len(picking.move_lines), 1)
        self.assertEquals(picking.carrier_id, self.carrier)
        picking.action_confirm()
        picking.action_assign()
        picking.send_to_shipper()
        self.assertEquals(
            picking.delivery_state, 'shipping_recorded_in_carrier')
        self.assertTrue(picking.date_shipped)
        self.assertFalse(picking.tracking_state_history)
        picking.tracking_state_update()
        picking.date_delivered = fields.Datetime.now()
        with self.assertRaises(NotImplementedError):
            picking.cancel_shipment()
        self.env['delivery.carrier']._patch_method(
            'fixed_cancel_shipment', lambda *args: True)
        picking.cancel_shipment()
        self.assertEquals(picking.delivery_state, 'canceled_shipment')
        self.assertFalse(picking.date_shipped)
        self.assertFalse(picking.date_delivered)

    def test_delivery_confirmation_send(self):
        """Check that the shipping notification is sent to the right partner"""
        self.env.ref(
            "delivery_state.delivery_notification").auto_delete = False
        self.sale.action_confirm()
        previous_mails = self.env["mail.mail"].search([
            ("partner_ids", "in", self.partner.ids)])
        self.assertFalse(previous_mails)
        picking = self.sale.picking_ids
        picking.company_id.send_delivery_confirmation = True
        picking.carrier_tracking_ref = "XX-0000"
        picking.move_lines.quantity_done = 1
        picking.action_done()
        mail = self.env["mail.mail"].search([
            ("partner_ids", "in", self.partner.ids)])
        self.assertTrue("XX-0000" in mail.body)
