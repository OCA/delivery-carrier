# Copyright 2017 Tecnativa - Luis M. Ontalba
# Copyright 2019-2020 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests import Form, common


class TestDeliveryMultiDestination(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.country_1 = cls.env["res.country"].create({"name": "Test country 1"})
        cls.partner_1 = cls.env["res.partner"].create(
            {
                "name": "Test partner 1",
                "country_id": cls.country_1.id,
            }
        )
        cls.country_2 = cls.env["res.country"].create({"name": "Test country 2"})
        cls.state = cls.env["res.country.state"].create(
            {"name": "Test state", "code": "TS", "country_id": cls.country_2.id}
        )
        cls.partner_2 = cls.env["res.partner"].create(
            {
                "name": "Test partner 2",
                "country_id": cls.country_2.id,
                "state_id": cls.state.id,
                "zip": "22222",
            }
        )
        cls.partner_3 = cls.env["res.partner"].create(
            {
                "name": "Test partner 3",
                "country_id": cls.country_2.id,
                "state_id": cls.state.id,
                "zip": "33333",
            }
        )
        cls.product = cls.env["product.product"].create(
            {"name": "Test carrier multi", "detailed_type": "service"}
        )
        cls.product_child_1 = cls.env["product.product"].create(
            {"name": "Test child 1", "detailed_type": "service"}
        )
        cls.product_child_2 = cls.env["product.product"].create(
            {"name": "Test child 2", "detailed_type": "service"}
        )
        cls.carrier_multi = cls._create_carrier(
            cls,
            (
                {
                    "name": "Test child 1",
                    "product_id": cls.product_child_1,
                    "zip_from": 20000,
                    "zip_to": 29999,
                    "delivery_type": "base_on_rule",
                    "price_rule_ids": [
                        {
                            "variable": "weight",
                            "operator": ">",
                            "max_value": 5,
                            "list_base_price": "70",
                        },
                        {
                            "variable": "weight",
                            "operator": "<=",
                            "max_value": 5,
                            "list_base_price": "50",
                        },
                    ],
                },
                {
                    "name": "Test child 2",
                    "product_id": cls.product_child_2,
                    "zip_from": 30000,
                    "zip_to": 39999,
                    "delivery_type": "fixed",
                    "fixed_price": 150,
                },
            ),
        )
        cls.carrier_single = cls.carrier_multi.copy(
            {
                "name": "Test carrier single",
                "destination_type": "one",
                "child_ids": False,
            }
        )
        cls.product = cls.env["product.product"].create(
            {"name": "Test product", "detailed_type": "product", "list_price": 1}
        )
        cls.purchase_order = cls._create_purchase_order(cls)

    def _create_carrier(self, childs):
        carrier_form = Form(self.env["delivery.carrier"])
        carrier_form.name = "Test carrier multi"
        carrier_form.product_id = self.product
        carrier_form.destination_type = "multi"
        carrier_form.delivery_type = "fixed"
        carrier_form.fixed_price = 100
        for child_item in childs:
            with carrier_form.child_ids.new() as child_form:
                child_form.name = child_item["name"]
                child_form.product_id = child_item["product_id"]
                child_form.country_ids.add(self.country_2)
                child_form.state_ids.add(self.state)
                child_form.zip_from = child_item["zip_from"]
                child_form.zip_to = child_item["zip_to"]
                child_form.delivery_type = child_item["delivery_type"]
                if child_item["delivery_type"] == "fixed":
                    child_form.fixed_price = child_item["fixed_price"]
                else:
                    for rule in child_item["price_rule_ids"]:
                        with child_form.price_rule_ids.new() as price_rule:
                            price_rule.variable = rule["variable"]
                            price_rule.operator = rule["operator"]
                            price_rule.max_value = rule["max_value"]
                            price_rule.list_base_price = rule["list_base_price"]
        return carrier_form.save()

    def _create_purchase_order(self):
        order_form = Form(self.env["purchase.order"])
        order_form.partner_id = self.partner_1
        with order_form.order_line.new() as line_form:
            line_form.product_id = self.product
        return order_form.save()

    def test_rate_shipment_multi_destination(self):
        order = self.purchase_order
        # When changing partner using carrier single should not change the delivery_price.
        order.carrier_id = self.carrier_single
        self.assertAlmostEqual(order.delivery_price, 100, 2)
        order.partner_id = self.partner_2
        self.assertAlmostEqual(order.delivery_price, 100, 2)
        # Using carrier multi, the price of delivery should depend on the partner selected
        order.carrier_id = self.carrier_multi
        self.assertAlmostEqual(order.delivery_price, 50, 2)
        order.partner_id = self.partner_3
        self.assertAlmostEqual(order.delivery_price, 150, 2)

    def test_picking_validation(self):
        self.purchase_order.carrier_id = self.carrier_multi.id
        self.purchase_order.partner_id = self.partner_2.id
        self.purchase_order.button_confirm()
        picking = self.purchase_order.picking_ids
        self.assertEqual(picking.carrier_id, self.carrier_multi)
        picking.move_lines.quantity_done = 1
        picking._action_done()
        self.assertAlmostEqual(picking.carrier_price, 50)

    def test_picking_validation_backorder(self):
        self.env["ir.config_parameter"].set_param(
            "delivery_purchase.use_delivered_qty_to_set_cost", "True"
        )
        self.product.weight = 1
        self.purchase_order.carrier_id = self.carrier_multi.id
        self.purchase_order.partner_id = self.partner_2.id
        self.purchase_order.order_line.product_qty = 10
        self.assertAlmostEqual(self.purchase_order.delivery_price, 70, 2)
        self.purchase_order.button_confirm()
        picking = self.purchase_order.picking_ids
        self.assertEqual(picking.carrier_id, self.carrier_multi)
        picking.move_lines.quantity_done = 4
        picking.with_context(cancel_backorder=False)._action_done()
        self.assertAlmostEqual(picking.carrier_price, 50)
        other_picking = self.purchase_order.picking_ids - picking
        other_picking.move_lines.filtered(
            lambda ml: ml.product_id == self.product
        ).quantity_done = 6
        other_picking._action_done()
        self.assertEqual(other_picking.carrier_price, 70)
