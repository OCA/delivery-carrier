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
