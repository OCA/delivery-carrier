# Copyright 2017 Tecnativa - Luis M. Ontalba
# Copyright 2019-2020 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.fields import Command
from odoo.tests import Form, common


class TestDeliveryMultiDestination(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.country_1 = cls.env["res.country"].create(
            {"name": "Test country 1", "code": "T1"}
        )
        cls.pricelist = cls.env["product.pricelist"].create(
            {"name": "Test pricelist", "currency_id": cls.env.company.currency_id.id}
        )
        cls.partner_1 = cls.env["res.partner"].create(
            {
                "name": "Test partner 1",
                "country_id": cls.country_1.id,
                "property_product_pricelist": cls.pricelist.id,
            }
        )
        cls.country_2 = cls.env["res.country"].create(
            {"name": "Test country 2", "code": "T2"}
        )
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
            {"name": "Test carrier multi", "type": "service"}
        )
        cls.product_child_1 = cls.env["product.product"].create(
            {"name": "Test child 1", "type": "service"}
        )
        cls.product_child_2 = cls.env["product.product"].create(
            {"name": "Test child 2", "type": "service"}
        )
        zip_prefix_child1 = cls.env["delivery.zip.prefix"].create({"name": "22222"})
        zip_prefix_child2 = cls.env["delivery.zip.prefix"].create({"name": "33333"})
        cls.carrier_multi = cls._create_carrier(
            cls,
            (
                {
                    "name": "Test child 1",
                    "product_id": cls.product_child_1,
                    "zip_prefix_ids": zip_prefix_child1,
                    "fixed_price": 50,
                },
                {
                    "name": "Test child 2",
                    "product_id": cls.product_child_2,
                    "zip_prefix_ids": zip_prefix_child2,
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
            {
                "name": "Test product",
                "type": "consu",
                "is_storable": True,
                "list_price": 1,
            }
        )
        cls.sale_order = cls._create_sale_order(cls)

    def _create_carrier(self, childs):
        carrier_form = Form(self.env["delivery.carrier"])
        carrier_form.name = "Test carrier multi"
        carrier_form.product_id = self.product
        carrier_form.delivery_type = "fixed"
        carrier_form.fixed_price = 100
        # this needs to be done in this order
        carrier_form.destination_type = "multi"
        for child_item in childs:
            with carrier_form.child_ids.new() as child_form:
                child_form.name = child_item["name"]
                child_form.product_id = child_item["product_id"]
                child_form.country_ids.add(self.country_2)
                child_form.state_ids.add(self.state)
                child_form.zip_prefix_ids.add(child_item["zip_prefix_ids"])
                child_form.delivery_type = "fixed"
                child_form.fixed_price = child_item["fixed_price"]
        return carrier_form.save()

    def _create_sale_order(self):
        order_form = Form(self.env["sale.order"])
        order_form.partner_id = self.partner_1
        with order_form.order_line.new() as line_form:
            line_form.product_id = self.product
        return order_form.save()

    def _choose_delivery_carrier(self, order, carrier):
        wizard = Form(
            self.env["choose.delivery.carrier"].with_context(
                **{
                    "default_order_id": order.id,
                    "default_carrier_id": carrier.id,
                }
            )
        )
        choose_delivery_carrier = wizard.save()
        choose_delivery_carrier.button_confirm()

    def test_delivery_multi_destination(self):
        order = self.sale_order
        order.carrier_id = self.carrier_single.id
        self._choose_delivery_carrier(order, order.carrier_id)
        sale_order_line = order.order_line.filtered("is_delivery")
        self.assertAlmostEqual(sale_order_line.price_unit, 100, 2)
        self.assertTrue(sale_order_line.is_delivery)
        order.carrier_id = self.carrier_multi.id
        order.partner_shipping_id = self.partner_2.id
        self._choose_delivery_carrier(order, order.carrier_id)
        sale_order_line = order.order_line.filtered("is_delivery")
        self.assertAlmostEqual(sale_order_line.price_unit, 50, 2)
        self.assertTrue(sale_order_line.is_delivery)
        order.partner_shipping_id = self.partner_3.id
        self._choose_delivery_carrier(order, order.carrier_id)
        sale_order_line = order.order_line.filtered("is_delivery")
        self.assertAlmostEqual(sale_order_line.price_unit, 150, 2)

    def test_search(self):
        carriers = self.env["delivery.carrier"].search([])
        children_carrier = self.carrier_multi.with_context(
            show_children_carriers=True,
        ).child_ids[0]
        self.assertNotIn(children_carrier, carriers)

    def test_name_search(self):
        carrier_names = self.env["delivery.carrier"].name_search()
        children_carrier = self.carrier_multi.with_context(
            show_children_carriers=True,
        ).child_ids[0]
        self.assertTrue(all(x[0] != children_carrier.id for x in carrier_names))

    def test_available_carriers(self):
        self.sale_order.partner_shipping_id = self.partner_2.id
        self.assertEqual(
            self.carrier_multi.available_carriers(self.partner_2, self.sale_order),
            self.carrier_multi,
        )

    def test_picking_validation(self):
        """Test a complete sales flow with picking."""
        self.sale_order.carrier_id = self.carrier_multi.id
        self.sale_order.partner_shipping_id = self.partner_2.id
        self.sale_order.action_confirm()
        picking = self.sale_order.picking_ids
        self.assertEqual(picking.carrier_id, self.carrier_multi)
        picking.move_ids.quantity = 1
        picking._action_done()
        self.assertAlmostEqual(picking.carrier_price, 50)

    def test_delivery_carrier_multi_form(self):
        carrier_form = Form(self.env["delivery.carrier"])
        carrier_form.name = "Multi carrier"
        carrier_form.destination_type = "multi"
        with carrier_form.child_ids.new() as child_form:
            child_form.name = "Child carrier"
            child_form.product_id = self.product_child_1
        carrier = carrier_form.save()
        self.assertEqual(carrier.product_id, self.product_child_1)

    def test_read_children_without_context(self):
        """Children carriers must stay readable outside of the
        ``show_children_carriers`` context (e.g. from an order)."""
        child = self.carrier_multi.with_context(
            show_children_carriers=True,
        ).child_ids[0]
        child.invalidate_recordset()
        self.assertEqual(
            self.env["delivery.carrier"].browse(child.id).name, "Test child 1"
        )
        self.sale_order.carrier_id = child
        self.sale_order.invalidate_recordset()
        self.assertEqual(self.sale_order.carrier_id.display_name, "Test child 1")
        # Recomputing fields on children must not raise an access error
        child.product_id.list_price = 75
        self.env.flush_all()

    def test_rate_shipment_no_destination(self):
        self.sale_order.partner_shipping_id = self.partner_1
        res = self.carrier_multi.rate_shipment(self.sale_order)
        self.assertFalse(res["success"])
        self.assertTrue(res["error_message"])

    def test_is_available_for_order(self):
        self.sale_order.partner_shipping_id = self.partner_2
        self.assertTrue(self.carrier_multi._is_available_for_order(self.sale_order))
        self.sale_order.partner_shipping_id = self.partner_1
        self.assertFalse(self.carrier_multi._is_available_for_order(self.sale_order))

    def test_picking_validation_base_on_rule(self):
        """Children based on rules get the price of the matching child."""
        child_2 = self.carrier_multi.with_context(
            show_children_carriers=True,
        ).child_ids[1]
        child_2.write(
            {
                "delivery_type": "base_on_rule",
                "price_rule_ids": [
                    Command.create(
                        {
                            "variable": "weight",
                            "operator": "<=",
                            "max_value": 1000,
                            "list_base_price": 70,
                        }
                    )
                ],
            }
        )
        self.sale_order.carrier_id = self.carrier_multi.id
        self.sale_order.partner_shipping_id = self.partner_3.id
        self.sale_order.action_confirm()
        picking = self.sale_order.picking_ids
        picking.move_ids.quantity = 1
        picking._action_done()
        self.assertAlmostEqual(picking.carrier_price, 70)
