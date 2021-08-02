# Copyright 2021 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.exceptions import UserError
from odoo.tests import Form, common


class TestDeliveryPrice(common.SavepointCase):
    def setUp(self):
        super().setUp()
        self.uom_m = self.env.ref("uom.product_uom_meter")
        self.product_a = self.env["product.product"].create(
            {"name": "Test product A", "volume": 1, "dimensional_uom_id": self.uom_m.id}
        )
        self.product_b = self.env["product.product"].create(
            {"name": "Test product B", "weight": 10}
        )
        self.product_shipping_cost = self.env["product.product"].create(
            {"name": "Shipping costs", "type": "service"}
        )
        self.carrier = self.env["delivery.carrier"].create(
            {
                "name": "Test carrier",
                "delivery_type": "base_on_rule",
                "product_id": self.product_shipping_cost.id,
                "price_rule_ids": [
                    (
                        0,
                        0,
                        {
                            "variable": "volumetric_weight",
                            "operator": ">",
                            "max_value": 100,
                            "list_base_price": 10,
                            "list_price": 1,
                            "variable_factor": "volumetric_weight",
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "variable": "weight",
                            "operator": ">",
                            "max_value": 10,
                            "list_base_price": 20,
                            "list_price": 1,
                            "variable_factor": "volumetric_weight",
                        },
                    ),
                ],
            }
        )
        self.partner = self.env["res.partner"].create({"name": "Test partner"})
        self.pricelist = self.env["product.pricelist"].create(
            {"name": "Test pricelist"}
        )
        self.sale = self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "pricelist_id": self.pricelist.id,
                "carrier_id": self.carrier.id,
                "order_line": [
                    (0, 0, {"product_id": self.product_a.id, "product_uom_qty": 1}),
                    (0, 0, {"product_id": self.product_b.id, "product_uom_qty": 1}),
                ],
            }
        )

    def _get_delivery_price_from_choose_delivery_carrier(self):
        delivery_wizard = Form(
            self.env["choose.delivery.carrier"].with_context(
                {"default_order_id": self.sale.id, "default_carrier_id": self.carrier}
            )
        )
        choose_delivery_carrier = delivery_wizard.save()
        return choose_delivery_carrier.delivery_price

    def test_delivery_price_without_rule_matching(self):
        with self.assertRaises(UserError):
            self.carrier._get_price_available(self.sale)

    def test_delivery_price_rule_weight(self):
        line_b = self.sale.order_line.filtered(lambda x: x.product_id == self.product_b)
        line_b.write({"product_uom_qty": 2})
        price = self.carrier._get_price_available(self.sale)
        # Total price: list_base_price + (list_price * total volumetric_weight)
        # Price: 20 + (1 * 100)
        self.assertEqual(price, 120.0)

    def test_delivery_price_rule_volumetric_weight(self):
        line_a = self.sale.order_line.filtered(lambda x: x.product_id == self.product_a)
        line_a.write({"product_uom_qty": 2})
        price = self.carrier._get_price_available(self.sale)
        # Total price: list_base_price + (list_price * total volumetric_weight)
        # Price: 10 + [1 * (100 * 2)]
        self.assertEqual(price, 210.0)
