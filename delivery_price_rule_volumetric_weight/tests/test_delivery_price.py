# Copyright 2021-2022 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
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
        self.carrier_hw = self.env["delivery.carrier"].create(
            {
                "name": "Test carrier (highest_weight)",
                "delivery_type": "base_on_rule",
                "product_id": self.product_shipping_cost.id,
                "price_rule_ids": [
                    (
                        0,
                        0,
                        {
                            "variable": "highest_weight",
                            "operator": ">",
                            "max_value": 10,
                            "list_base_price": 5,
                            "list_price": 1,
                            "variable_factor": "highest_weight",
                        },
                    ),
                ],
            }
        )
        self.carrier = self.env["delivery.carrier"].create(
            {
                "name": "Test carrier (weight and volumetric_weight)",
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
                            "variable_factor": "weight",
                        },
                    ),
                ],
            }
        )
        self.pricelist = self.env["product.pricelist"].create(
            {"name": "Test pricelist"}
        )
        self.partner = self.env["res.partner"].create(
            {"name": "Test partner", "property_product_pricelist": self.pricelist.id}
        )

    def _create_sale_order(self, product):
        order_form = Form(self.env["sale.order"])
        order_form.partner_id = self.partner
        with order_form.order_line.new() as so_line_form:
            so_line_form.product_id = product
        return order_form.save()

    def _get_delivery_price_from_choose_delivery_carrier(self, order, carrier):
        delivery_wizard = Form(
            self.env["choose.delivery.carrier"].with_context(
                {"default_order_id": order.id, "default_carrier_id": carrier}
            )
        )
        choose_delivery_carrier = delivery_wizard.save()
        return choose_delivery_carrier.delivery_price

    def test_delivery_price_rule_highest_weight_1(self):
        order = self._create_sale_order(self.product_a)
        order.order_line.write({"product_uom_qty": 2})
        price = self._get_delivery_price_from_choose_delivery_carrier(
            order, self.carrier_hw
        )
        # Total price: list_base_price + (list_price * total volumetric_weight)
        # Price: 5 + [1 * (100 * 2)]
        self.assertEqual(price, 205.0)

    def test_delivery_price_rule_highest_weight_2(self):
        self.product_a.weight = 200
        order = self._create_sale_order(self.product_a)
        order.order_line.write({"product_uom_qty": 2})
        price = self._get_delivery_price_from_choose_delivery_carrier(
            order, self.carrier_hw
        )
        # Total price: list_base_price + (list_price * total weight)
        # Price: 5 + [1 * (200 * 2)]
        self.assertEqual(price, 405.0)

    def test_delivery_price_rule_weight(self):
        order = self._create_sale_order(self.product_b)
        order.order_line.write({"product_uom_qty": 2})
        price = self._get_delivery_price_from_choose_delivery_carrier(
            order, self.carrier
        )
        # Total price: list_base_price + (list_price * total weight)
        # Price: 20 + [1 * (10 * 2)]
        self.assertEqual(price, 40.0)

    def test_delivery_price_rule_volumetric_weight(self):
        order = self._create_sale_order(self.product_a)
        order.order_line.write({"product_uom_qty": 2})
        price = self._get_delivery_price_from_choose_delivery_carrier(
            order, self.carrier
        )
        # Total price: list_base_price + (list_price * total volumetric_weight)
        # Price: 10 + [1 * (100 * 2)]
        self.assertEqual(price, 210.0)
