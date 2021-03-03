# Copyright 2018 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.fields import first
from odoo.tests import Form, common


class TestDeliveryAutoRefresh(common.SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.Param = cls.env["ir.config_parameter"].sudo()
        cls.Product = cls.env["product.product"]
        cls.Partner = cls.env["res.partner"]
        cls.Carrier = cls.env["delivery.carrier"]
        cls.SaleOrder = cls.env["sale.order"]
        service = cls.Product.create({"name": "Service Test", "type": "service"})
        cls.carrier = cls.Carrier.create(
            {
                "name": "Test carrier",
                "delivery_type": "base_on_rule",
                "product_id": service.id,
                "price_rule_ids": [
                    (
                        0,
                        0,
                        {
                            "variable": "weight",
                            "operator": "<=",
                            "max_value": 20,
                            "list_base_price": 50,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "variable": "weight",
                            "operator": "<=",
                            "max_value": 40,
                            "list_base_price": 30,
                            "list_price": 1,
                            "variable_factor": "weight",
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "variable": "weight",
                            "operator": ">",
                            "max_value": 40,
                            "list_base_price": 20,
                            "list_price": 1.5,
                            "variable_factor": "weight",
                        },
                    ),
                ],
            }
        )
        cls.product = cls.Product.create(
            {"name": "Test product", "weight": 10, "list_price": 20}
        )
        cls.partner = cls.Partner.create(
            {"name": "Test partner", "property_delivery_carrier_id": cls.carrier.id}
        )
        cls.param_name1 = "delivery_auto_refresh.auto_add_delivery_line"
        cls.param_name2 = "delivery_auto_refresh.refresh_after_picking"
        with Form(cls.SaleOrder) as new_so:
            new_so.partner_id = cls.partner
            new_so.partner_shipping_id = cls.partner
            with new_so.order_line.new() as new_line:
                new_line.product_id = cls.product
                new_line.product_uom_qty = 2
        cls.order = new_so.save()

    def _add_carrier(self, sale_order, carrier):
        """
        Add a carrier on the SO using wizard
        :param sale_order: sale.order recordset
        :param carrier: delivery.carrier recordset
        :return: None
        """
        action = sale_order.action_open_delivery_wizard()
        wizard_ctx = action.get('context', {})
        wizard_model = action.get("res_model")
        wizard = self.env[wizard_model].with_context(wizard_ctx).create(
            {"order_id": sale_order.id, "carrier_id": carrier.id}
        )
        wizard._get_shipment_rate()
        wizard.button_confirm()

    def test_auto_refresh_so(self):
        self.assertFalse(self.order.order_line.filtered("is_delivery"))
        self.Param.set_param(self.param_name1, 1)
        self._add_carrier(self.order, self.carrier)
        with Form(self.order) as order:
            with order.order_line.edit(0) as line_form:
                line_form.product_uom_qty = 3
            line_form.save()
        line_delivery = self.order.order_line.filtered("is_delivery")
        self.assertTrue(line_delivery)
        self.assertEqual(line_delivery.price_unit, 60)
        with Form(self.order) as order:
            with order.order_line.new() as new_line:
                new_line.product_id = self.product
                new_line.product_uom_qty = 2
            new_line.save()
        line_delivery = self.order.order_line.filtered("is_delivery")
        self.assertTrue(line_delivery)
        self.assertEqual(line_delivery.price_unit, 95)

    def test_auto_refresh_picking(self):
        self.Param.set_param(self.param_name2, 1)
        self._add_carrier(self.order, self.carrier)
        with Form(self.order) as order:
            with order.order_line.edit(0) as line_form:
                line_form.product_uom_qty = 3
        self.order.action_confirm()
        picking = self.order.picking_ids
        picking.action_assign()
        first(picking.move_line_ids).qty_done = 2
        picking.action_done()
        line_delivery = self.order.order_line.filtered("is_delivery")
        self.assertTrue(line_delivery)
        self.assertEqual(line_delivery.price_unit, 50)

    def test_no_auto_refresh_picking(self):
        self.Param.set_param(self.param_name2, "0")
        self._add_carrier(self.order, self.carrier)
        with Form(self.order) as order:
            with order.order_line.edit(0) as line_form:
                line_form.product_uom_qty = 3
        self.order.action_confirm()
        picking = self.order.picking_ids
        picking.action_assign()
        with Form(picking.move_line_ids) as move_line:
            move_line.qty_done = 2
        move_line.save()
        picking.action_done()
        line_delivery = self.order.order_line.filtered("is_delivery")
        self.assertTrue(line_delivery)
        self.assertEqual(line_delivery.price_unit, 60)
