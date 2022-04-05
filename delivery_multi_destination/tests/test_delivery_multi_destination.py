# Copyright 2017 Luis M. Ontalba <luis.martinez@tecnativa.com>
# Copyright 2019-2020 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests import Form, common


class TestDeliveryMultiDestination(common.SavepointCase):
    @classmethod
    def setUpClass(cls):
        super(TestDeliveryMultiDestination, cls).setUpClass()
        cls.country_1 = cls.env["res.country"].create({"name": "Test country 1"})
        cls.partner_1 = cls.env["res.partner"].create(
            {"name": "Test partner 1", "country_id": cls.country_1.id}
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
            {"name": "Test carrier multi", "type": "service"}
        )
        cls.product_child_1 = cls.env["product.product"].create(
            {"name": "Test child 1", "type": "service"}
        )
        cls.product_child_2 = cls.env["product.product"].create(
            {"name": "Test child 2", "type": "service"}
        )
        cls.carrier_multi = cls.env["delivery.carrier"].create(
            {
                "name": "Test carrier multi",
                "product_id": cls.product.id,
                "destination_type": "multi",
                "delivery_type": "fixed",
                "fixed_price": 100,
                "child_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "Test child 1",
                            "product_id": cls.product_child_1.id,
                            "sequence": 1,
                            "country_ids": [(6, 0, cls.country_2.ids)],
                            "state_ids": [(6, 0, cls.state.ids)],
                            "zip_from": 20000,
                            "zip_to": 29999,
                            "delivery_type": "fixed",
                            "fixed_price": 50,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "name": "Test child 2",
                            "product_id": cls.product_child_2.id,
                            "sequence": 2,
                            "country_ids": [(6, 0, cls.country_2.ids)],
                            "state_ids": [(6, 0, cls.state.ids)],
                            "zip_from": 30000,
                            "zip_to": 39999,
                            "delivery_type": "fixed",
                            "fixed_price": 150,
                        },
                    ),
                ],
            }
        )
        cls.carrier_single = cls.carrier_multi.copy(
            {
                "name": "Test carrier single",
                "destination_type": "one",
                "child_ids": False,
            }
        )
        cls.product = cls.env["product.product"].create(
            {"name": "Test product", "type": "product"}
        )
        cls.pricelist = cls.env["product.pricelist"].create(
            {
                "name": "Test pricelist",
                "item_ids": [
                    (
                        0,
                        0,
                        {
                            "applied_on": "3_global",
                            "compute_price": "formula",
                            "base": "list_price",
                        },
                    )
                ],
            }
        )
        cls.sale_order = cls.env["sale.order"].create(
            {
                "partner_id": cls.partner_1.id,
                "picking_policy": "direct",
                "pricelist_id": cls.pricelist.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "name": "Test",
                            "product_id": cls.product.id,
                            "product_uom_qty": 1,
                            "price_unit": 1,
                        },
                    ),
                ],
            }
        )

    def test_delivery_multi_destination(self):
        order = self.sale_order
        order.carrier_id = self.carrier_single.id
        delivery_wizard = Form(
            self.env["choose.delivery.carrier"].with_context(
                {
                    "default_order_id": order.id,
                    "default_carrier_id": order.carrier_id.id,
                }
            )
        )
        choose_delivery_carrier = delivery_wizard.save()
        choose_delivery_carrier.button_confirm()
        sale_order_line = order.order_line.filtered("is_delivery")
        self.assertAlmostEqual(sale_order_line.price_unit, 100, 2)
        self.assertTrue(sale_order_line.is_delivery)
        order.carrier_id = self.carrier_multi.id
        order.partner_shipping_id = self.partner_2.id
        delivery_wizard = Form(
            self.env["choose.delivery.carrier"].with_context(
                {
                    "default_order_id": order.id,
                    "default_carrier_id": order.carrier_id.id,
                }
            )
        )
        choose_delivery_carrier = delivery_wizard.save()
        choose_delivery_carrier.button_confirm()
        sale_order_line = order.order_line.filtered("is_delivery")
        self.assertAlmostEqual(sale_order_line.price_unit, 50, 2)
        self.assertTrue(sale_order_line.is_delivery)
        order.partner_shipping_id = self.partner_3.id
        delivery_wizard = Form(
            self.env["choose.delivery.carrier"].with_context(
                {
                    "default_order_id": order.id,
                    "default_carrier_id": order.carrier_id.id,
                }
            )
        )
        choose_delivery_carrier = delivery_wizard.save()
        choose_delivery_carrier.button_confirm()
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
        self.assertEqual(
            self.carrier_multi.available_carriers(self.partner_2),
            self.carrier_multi,
        )

    def test_picking_validation(self):
        """Test a complete sales flow with picking."""
        self.sale_order.carrier_id = self.carrier_multi.id
        self.sale_order.partner_shipping_id = self.partner_2.id
        self.sale_order.action_confirm()
        picking = self.sale_order.picking_ids
        self.assertEqual(picking.carrier_id, self.carrier_multi)
        picking.move_lines.quantity_done = 1
        picking._action_done()
        self.assertAlmostEqual(picking.carrier_price, 50)
