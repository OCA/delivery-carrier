# Copyright 2020 Trey, Kilobytes de Soluciones
# Copyright 2020 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.tests import Form
from odoo.tests.common import SavepointCase
from odoo.tools import float_compare


class TestDeliveryPriceMethod(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        self = cls
        product_shipping_cost = self.env["product.product"].create(
            {
                "type": "service",
                "name": "Shipping costs",
                "standard_price": 10,
                "list_price": 100,
            }
        )
        self.carrier = self.env["delivery.carrier"].create(
            {
                "name": "Test carrier",
                "delivery_type": "fixed",
                "product_id": product_shipping_cost.id,
                "fixed_price": 99.99,
            }
        )
        self.pricelist = self.env["product.pricelist"].create(
            {
                "name": "Test pricelist",
                "item_ids": [(0, 0, {"applied_on": "3_global", "base": "list_price"})],
            }
        )
        self.product = self.env.ref("product.product_delivery_01")
        self.partner = self.env.ref("base.res_partner_12")
        self.sale = self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "pricelist_id": self.pricelist.id,
                "carrier_id": self.carrier.id,
                "order_line": [
                    (0, 0, {"product_id": self.product.id, "product_uom_qty": 1})
                ],
            }
        )

    def _add_delivery(self):
        sale = self.sale
        delivery_wizard = Form(
            self.env["choose.delivery.carrier"].with_context(
                {"default_order_id": sale.id, "default_carrier_id": self.carrier}
            )
        )
        choose_delivery_carrier = delivery_wizard.save()
        choose_delivery_carrier.button_confirm()

    def test_delivery_price_fixed(self):
        sale = self.sale
        self._add_delivery()
        delivery_lines = sale.order_line.filtered(lambda r: r.is_delivery)
        delivery_price = sum(delivery_lines.mapped("price_unit"))
        self.assertEqual(float_compare(delivery_price, 99.99, precision_digits=2), 0)
        self.assertEquals(len(delivery_lines), 1)
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
        self.carrier.write({"price_method": "fixed", "fixed_price": 99.99})
        sale = self.sale
        self._add_delivery()
        delivery_lines = sale.order_line.filtered(lambda r: r.is_delivery)
        delivery_price = sum(delivery_lines.mapped("price_unit"))
        self.assertEqual(float_compare(delivery_price, 99.99, precision_digits=2), 0)
        self.assertEquals(len(delivery_lines), 1)
        self.carrier.write({"price_method": "fixed", "fixed_price": 5})
        self._add_delivery()
        delivery_lines = sale.order_line.filtered(lambda r: r.is_delivery)
        delivery_price = sum(delivery_lines.mapped("price_unit"))
        self.assertEquals(delivery_price, 5)
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
        self.assertEquals(delivery_price, 11.11)
