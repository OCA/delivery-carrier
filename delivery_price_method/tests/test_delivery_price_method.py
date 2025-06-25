# Copyright 2020 Trey, Kilobytes de Soluciones
# Copyright 2020 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tools import float_compare

from .common import TestDeliveryPriceMethodCommon


class TestDeliveryPriceMethod(TestDeliveryPriceMethodCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def test_01_delivery_price_fixed(self):
        sale = self.sale
        self._add_delivery()
        delivery_lines = sale.order_line.filtered(lambda r: r.is_delivery)
        delivery_price = sum(delivery_lines.mapped("price_unit"))
        self.assertEqual(float_compare(delivery_price, 99.99, precision_digits=2), 0)
        self.assertEqual(len(delivery_lines), 1)
        sale.action_confirm()
        picking = sale.picking_ids[0]
        picking.move_ids.quantity = 1
        self.assertEqual(len(picking.move_line_ids), 1)
        self.assertEqual(picking.carrier_id, self.carrier)
        picking.action_confirm()
        picking.action_assign()
        self.assertFalse(picking.carrier_price)
        picking.send_to_shipper()
        self.assertEqual(picking.carrier_price, 99.99)

    def test_02_delivery_price_method(self):
        self.carrier.write({"price_method": "fixed", "fixed_price": 99.99})
        sale = self.sale
        self._add_delivery()
        delivery_lines = sale.order_line.filtered(lambda r: r.is_delivery)
        delivery_price = sum(delivery_lines.mapped("price_unit"))
        self.assertEqual(float_compare(delivery_price, 99.99, precision_digits=2), 0)
        self.assertEqual(len(delivery_lines), 1)
        self.carrier.write({"price_method": "fixed", "fixed_price": 5})
        self._add_delivery()
        delivery_lines = sale.order_line.filtered(lambda r: r.is_delivery)
        delivery_price = sum(delivery_lines.mapped("price_unit"))
        self.assertEqual(delivery_price, 5)
        self.carrier.write(
            {
                "price_method": "base_on_rule",
                "price_rule_ids": [
                    (
                        0,
                        0,
                        {
                            "variable": "quantity",
                            "operator": "==",
                            "max_value": 1,
                            "list_base_price": 11.11,
                        },
                    )
                ],
            }
        )
        self._add_delivery()
        delivery_lines = sale.order_line.filtered(lambda r: r.is_delivery)
        delivery_price = sum(delivery_lines.mapped("price_unit"))
        self.assertEqual(delivery_price, 11.11)

    def test_03_delivery_price_method_free_over(self):
        free_price = self.carrier_free._get_price_from_picking(
            total=50, weight=20, volume=10, quantity=10, wv=0.0
        )
        self.assertEqual(free_price, 0.0)
        prices = self.carrier_free.rate_shipment(self.sale_2)
        self.assertEqual(prices["price"], 0.0)
        self.assertEqual(prices["carrier_price"], 0.0)
        self.carrier_free.write(
            {
                "price_method": "base_on_rule",
                "amount": 100,
                "free_over": False,
                "price_rule_ids": [
                    (
                        0,
                        0,
                        {
                            "variable": "quantity",
                            "operator": "==",
                            "max_value": 1,
                            "list_base_price": 11.11,
                        },
                    )
                ],
            }
        )
        base_price = self.carrier_free._get_price_from_picking(
            total=70.0, weight=0.01, volume=0.0, quantity=1.0, wv=0.0
        )
        prices = self.carrier_free.rate_shipment(self.sale_2)
        self.assertEqual(prices["price"], 11.11)
        self.assertEqual(prices["carrier_price"], 11.11)
        self.assertEqual(base_price, 11.11)
