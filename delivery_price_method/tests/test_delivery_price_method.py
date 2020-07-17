# Copyright 2020 Trey, Kilobytes de Soluciones
# Copyright 2020 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.tests.common import SavepointCase


class TestDeliveryPriceMethod(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        self = cls
        product_shipping_cost = self.env['product.product'].create({
            'type': 'service',
            'name': 'Shipping costs',
            'standard_price': 10,
            'list_price': 100,
        })
        self.carrier = self.env['delivery.carrier'].create({
            'name': 'Test carrier',
            'delivery_type': 'fixed',
            'product_id': product_shipping_cost.id,
            'fixed_price': 99.99,
        })
        self.pricelist = self.env["product.pricelist"].create({
            "name": "Test pricelist",
            "item_ids": [(0, 0, {
                "applied_on": "3_global",
                "base": "list_price",
            })],
        })
        self.product = self.env.ref('product.product_delivery_01')
        self.partner = self.env.ref('base.res_partner_12')
        self.sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'pricelist_id': self.pricelist.id,
            'carrier_id': self.carrier.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': 1})]
        })

    def test_delivery_price_fixed(self):
        sale = self.sale
        sale.get_delivery_price()
        self.assertEquals(sale.delivery_price, 99.99)
        sale.set_delivery_line()
        self.assertEquals(len(sale.order_line), 2)
        sale.action_confirm()
        picking = sale.picking_ids[0]
        self.assertEquals(len(picking.move_lines), 1)
        self.assertEquals(picking.carrier_id, self.carrier)
        picking.action_confirm()
        picking.action_assign()
        self.assertFalse(picking.carrier_price)
        picking.send_to_shipper()
        self.assertEquals(picking.carrier_price, 99.99)

    def test_delivery_price_method(self):
        self.carrier.write({
            'price_method': 'fixed',
            'fixed_price': 99.99,
        })
        sale = self.sale
        sale.get_delivery_price()
        self.assertEquals(sale.delivery_price, 99.99)
        self.carrier.write({
            'price_method': 'fixed',
            'fixed_price': 5,
        })
        sale.get_delivery_price()
        self.assertEquals(sale.delivery_price, 5)
        self.carrier.write({
            'price_method': 'base_on_rule',
            'price_rule_ids': [(0, 0, {
                'variable': 'quantity',
                'operator': '==',
                'max_value': 1,
                'list_base_price': 11.11})]
        })
        sale.get_delivery_price()
        self.assertEquals(sale.delivery_price, 11.11)
