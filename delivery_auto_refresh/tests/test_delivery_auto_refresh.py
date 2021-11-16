# Copyright 2018 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests import Form, common


def _execute_onchanges(records, field_name):
    """Helper methods that executes all onchanges associated to a field."""
    for onchange in records._onchange_methods.get(field_name, []):
        for record in records:
            onchange(record)


class TestDeliveryAutoRefresh(common.HttpCase):
    def setUp(self):
        super().setUp()
        service = self.env["product.product"].create(
            {"name": "Service Test", "type": "service"}
        )
        pricelist = self.env["product.pricelist"].create(
            {"name": "Test pricelist", "currency_id": self.env.company.currency_id.id}
        )
        carrier_form = Form(self.env["delivery.carrier"])
        carrier_form.name = "Test carrier 1"
        carrier_form.delivery_type = "base_on_rule"
        carrier_form.product_id = service
        with carrier_form.price_rule_ids.new() as price_rule_form:
            price_rule_form.variable = "weight"
            price_rule_form.operator = "<="
            price_rule_form.max_value = 20
            price_rule_form.list_base_price = 50
        with carrier_form.price_rule_ids.new() as price_rule_form:
            price_rule_form.variable = "weight"
            price_rule_form.operator = "<="
            price_rule_form.max_value = 40
            price_rule_form.list_base_price = 30
            price_rule_form.list_price = 1
            price_rule_form.variable_factor = "weight"
        with carrier_form.price_rule_ids.new() as price_rule_form:
            price_rule_form.variable = "weight"
            price_rule_form.operator = ">"
            price_rule_form.max_value = 40
            price_rule_form.list_base_price = 20
            price_rule_form.list_price = 1.5
            price_rule_form.variable_factor = "weight"
        self.carrier_1 = carrier_form.save()
        carrier_form = Form(self.env["delivery.carrier"])
        carrier_form.name = "Test carrier 2"
        carrier_form.delivery_type = "base_on_rule"
        carrier_form.product_id = service
        with carrier_form.price_rule_ids.new() as price_rule_form:
            price_rule_form.variable = "weight"
            price_rule_form.operator = "<="
            price_rule_form.max_value = 20
            price_rule_form.list_base_price = 50
        self.carrier_2 = carrier_form.save()
        self.product = self.env["product.product"].create(
            {"name": "Test product", "weight": 10, "list_price": 20}
        )
        self.partner = self.env["res.partner"].create(
            {
                "name": "Test partner",
                "property_delivery_carrier_id": self.carrier_1.id,
                "property_product_pricelist": pricelist.id,
            }
        )
        self.param_name1 = "delivery_auto_refresh.auto_add_delivery_line"
        self.param_name2 = "delivery_auto_refresh.refresh_after_picking"
        order_form = Form(self.env["sale.order"])
        order_form.partner_id = self.partner
        order_form.partner_shipping_id = self.partner
        with order_form.order_line.new() as ol_form:
            ol_form.product_id = self.product
            ol_form.product_uom_qty = 2
        self.order = order_form.save()

    def test_auto_refresh_so(self):
        self.assertFalse(self.order.order_line.filtered("is_delivery"))
        self.env["ir.config_parameter"].sudo().set_param(self.param_name1, 1)
        self.order.write(
            {"order_line": [(1, self.order.order_line.id, {"product_uom_qty": 3})]}
        )
        line_delivery = self.order.order_line.filtered("is_delivery")
        self.assertEqual(line_delivery.price_unit, 60)
        line2 = self.order.order_line.new(
            {
                "order_id": self.order.id,
                "product_id": self.product.id,
                "product_uom_qty": 2,
            }
        )
        _execute_onchanges(line2, "product_id")
        vals = line2._convert_to_write(line2._cache)
        del vals["order_id"]
        self.order.write({"order_line": [(0, 0, vals)]})
        line_delivery = self.order.order_line.filtered("is_delivery")
        self.assertEqual(line_delivery.price_unit, 95)
        # Test saving the discount
        line_delivery.discount = 10
        self.order.carrier_id = self.carrier_2
        line_delivery = self.order.order_line.filtered("is_delivery")
        self.assertEqual(line_delivery.discount, 10)
        # Test change the carrier_id using the wizard
        wiz = Form(
            self.env["choose.delivery.carrier"].with_context(
                {
                    "default_order_id": self.order.id,
                    "default_carrier_id": self.carrier_1.id,
                }
            )
        ).save()
        wiz.button_confirm()
        self.assertEqual(self.order.carrier_id, self.carrier_1)
        line_delivery = self.order.order_line.filtered("is_delivery")
        self.assertEqual(line_delivery.name, "Test carrier 1")

    def test_auto_refresh_picking(self):
        self.env["ir.config_parameter"].sudo().set_param(self.param_name2, 1)
        self.order.order_line.product_uom_qty = 3
        wiz = Form(
            self.env["choose.delivery.carrier"].with_context(
                {
                    "default_order_id": self.order.id,
                    "default_carrier_id": self.carrier_1.id,
                }
            )
        ).save()
        wiz.button_confirm()
        self.order.action_confirm()
        picking = self.order.picking_ids
        picking.action_assign()
        picking.move_line_ids[0].qty_done = 2
        picking._action_done()
        line_delivery = self.order.order_line.filtered("is_delivery")
        self.assertEqual(line_delivery.price_unit, 50)

    def test_no_auto_refresh_picking(self):
        self.env["ir.config_parameter"].sudo().set_param(self.param_name2, "0")
        self.order.order_line.product_uom_qty = 3
        wiz = Form(
            self.env["choose.delivery.carrier"].with_context(
                {
                    "default_order_id": self.order.id,
                    "default_carrier_id": self.carrier_1.id,
                }
            )
        ).save()
        wiz.button_confirm()
        self.order.action_confirm()
        picking = self.order.picking_ids
        picking.action_assign()
        picking.move_line_ids[0].qty_done = 2
        picking._action_done()
        line_delivery = self.order.order_line.filtered("is_delivery")
        self.assertEqual(line_delivery.price_unit, 60)

    def test_compute_carrier_id(self):
        order_form_1 = Form(self.env["sale.order"])
        order_form_1.partner_id = self.partner
        self.assertEqual(order_form_1.carrier_id, self.carrier_1)
        partner_without_carrier = self.env["res.partner"].create(
            {
                "name": "Test partner without carrier",
                "property_delivery_carrier_id": False,
            }
        )
        no_carrier = self.env["delivery.carrier"]
        order_form_2 = Form(self.env["sale.order"])
        order_form_2.partner_id = partner_without_carrier
        self.assertEqual(order_form_2.carrier_id, no_carrier)
