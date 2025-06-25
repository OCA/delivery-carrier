# Copyright 2018-2023 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests import Form, tagged
from odoo.tools import mute_logger

from odoo.addons.base.tests.common import BaseCommon


def _execute_onchanges(records, field_name):
    """Helper methods that executes all onchanges associated to a field."""
    for onchange in records._onchange_methods.get(field_name, []):
        for record in records:
            onchange(record)


@tagged("post_install", "-at_install")
class TestDeliveryAutoRefresh(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.service = cls.env["product.product"].create(
            {"name": "Service Test", "type": "service"}
        )
        pricelist = cls.env["product.pricelist"].create(
            {"name": "Test pricelist", "currency_id": cls.env.company.currency_id.id}
        )
        carrier_form = Form(cls.env["delivery.carrier"])
        carrier_form.name = "Test carrier 1"
        carrier_form.delivery_type = "base_on_rule"
        carrier_form.product_id = cls.service
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
        cls.carrier_1 = carrier_form.save()
        carrier_form = Form(cls.env["delivery.carrier"])
        carrier_form.name = "Test carrier 2"
        carrier_form.delivery_type = "base_on_rule"
        carrier_form.product_id = cls.service
        with carrier_form.price_rule_ids.new() as price_rule_form:
            price_rule_form.variable = "weight"
            price_rule_form.operator = "<="
            price_rule_form.max_value = 20
            price_rule_form.list_base_price = 50
        cls.carrier_2 = carrier_form.save()
        cls.product = cls.env["product.product"].create(
            {
                "name": "Test product",
                "type": "consu",
                "weight": 10,
                "list_price": 20,
            }
        )
        cls.partner = cls.env["res.partner"].create(
            {
                "name": "Test partner",
                "property_delivery_carrier_id": cls.carrier_1.id,
                "property_product_pricelist": pricelist.id,
            }
        )
        cls.settings = cls.env["res.config.settings"].create({})
        cls.settings.execute()
        order_form = Form(cls.env["sale.order"])
        order_form.partner_id = cls.partner
        with order_form.order_line.new() as ol_form:
            ol_form.product_id = cls.product
            ol_form.product_uom_qty = 2
        cls.order = order_form.save()

    def test_auto_refresh_so(self):
        self.assertFalse(self.order.order_line.filtered("is_delivery"))
        self.settings.sale_auto_add_delivery_line = True
        self.settings.execute()
        sale_form = Form(self.order)
        with sale_form.order_line.edit(0) as line_form:
            line_form.product_uom_qty = 3
        sale_form.save()
        line_delivery = self.order.order_line.filtered("is_delivery")
        self.assertEqual(line_delivery.price_unit, 60)
        with sale_form.order_line.new() as line_form:
            line_form.product_id = self.product
            line_form.product_uom_qty = 2
        sale_form.save()
        self.assertEqual(line_delivery.price_unit, 95)
        # Test saving the discount
        line_delivery.discount = 10
        self.order.carrier_id = self.carrier_2
        self.assertEqual(line_delivery.discount, 10)
        # Test change the carrier_id using the wizard
        wiz = Form(
            self.env["choose.delivery.carrier"].with_context(
                default_order_id=self.order.id,
                default_carrier_id=self.carrier_1.id,
            )
        ).save()
        wiz.button_confirm()
        self.assertEqual(self.order.carrier_id, self.carrier_1)
        self.assertEqual(line_delivery.name, "Test carrier 1")

    def test_auto_refresh_picking(self):
        self.settings.sale_refresh_delivery_after_picking = True
        self.settings.execute()
        self.order.order_line.product_uom_qty = 3
        wiz = Form(
            self.env["choose.delivery.carrier"].with_context(
                default_order_id=self.order.id,
                default_carrier_id=self.carrier_1.id,
            )
        ).save()
        wiz.button_confirm()
        self.order.action_confirm()
        picking = self.order.picking_ids
        picking.action_assign()
        picking.move_ids.quantity = 2
        backorder_wiz = picking.button_validate()
        backorder_wiz = Form(
            self.env[backorder_wiz["res_model"]].with_context(
                **backorder_wiz["context"]
            )
        ).save()
        backorder_wiz.process()
        self.assertEqual(picking.state, "done")
        line_delivery = self.order.order_line.filtered("is_delivery")
        self.assertEqual(line_delivery.price_unit, 50)

    def test_auto_refresh_picking_fixed_price(self):
        self.settings.sale_refresh_delivery_after_picking = True
        self.settings.execute()
        carrier_form = Form(self.env["delivery.carrier"])
        carrier_form.name = self.service.name
        carrier_form.product_id = self.service
        carrier_form.delivery_type = "fixed"
        carrier_form.fixed_price = 2
        carrier_fixed_price = carrier_form.save()
        wiz = Form(
            self.env["choose.delivery.carrier"].with_context(
                default_order_id=self.order.id,
                default_carrier_id=carrier_fixed_price.id,
            )
        ).save()
        wiz.button_confirm()
        self.order.action_confirm()
        self.order.action_lock()  # Lock order to check writing protection disabling
        picking = self.order.picking_ids
        picking.action_assign()
        picking.move_ids.quantity = 2
        picking.button_validate()
        self.assertEqual(picking.state, "done")
        line_delivery = self.order.order_line.filtered("is_delivery")
        self.assertEqual(line_delivery.price_unit, 2)

    def test_no_auto_refresh_picking(self):
        self.settings.sale_refresh_delivery_after_picking = False
        self.settings.execute()
        self.order.order_line.product_uom_qty = 3
        wiz = Form(
            self.env["choose.delivery.carrier"].with_context(
                default_order_id=self.order.id,
                default_carrier_id=self.carrier_1.id,
            )
        ).save()
        wiz.button_confirm()
        self.order.action_confirm()
        picking = self.order.picking_ids
        picking.action_assign()
        picking.move_ids.quantity = 2
        backorder_wiz = picking.button_validate()
        backorder_wiz = Form(
            self.env[backorder_wiz["res_model"]].with_context(
                **backorder_wiz["context"]
            )
        ).save()
        backorder_wiz.process()
        self.assertEqual(picking.state, "done")
        line_delivery = self.order.order_line.filtered("is_delivery")
        self.assertEqual(line_delivery.price_unit, 60)

    def _confirm_sale_order(self, order):
        sale_form = Form(order)
        # Force the delivery line creation
        with sale_form.order_line.edit(0) as line_form:
            line_form.product_uom_qty = 2
        sale_form.save()
        line_delivery = order.order_line.filtered("is_delivery")
        order.action_confirm()
        return line_delivery

    def _validate_picking(self, picking):
        """Helper method to confirm the pickings"""
        for line in picking.move_ids:
            line.quantity = line.product_uom_qty
        picking.button_validate()

    def _return_whole_picking(self, picking, to_refund=True):
        """Helper method to create a return of the original picking. It could
        be refundable or not"""
        return_wiz_form = Form(
            self.env["stock.return.picking"].with_context(
                active_ids=picking.ids,
                active_id=picking[:1].id,
                active_model="stock.picking",
            )
        )
        return_wiz = return_wiz_form.save()
        return_wiz.product_return_moves.quantity = picking.move_ids.quantity
        return_wiz.product_return_moves.to_refund = to_refund
        res = return_wiz.action_create_returns()
        return_picking = self.env["stock.picking"].browse(res["res_id"])
        self._validate_picking(return_picking)

    def _test_autorefresh_void_line(self, lock=False, to_refund=True, invoice=False):
        """Helper method to test the possible cases for voiding the line"""
        self.assertFalse(self.order.order_line.filtered("is_delivery"))
        self.settings.sale_auto_add_delivery_line = True
        self.settings.sale_auto_void_delivery_line = True
        self.settings.execute()
        line_delivery = self._confirm_sale_order(self.order)
        self._validate_picking(self.order.picking_ids)
        if invoice:
            self.order._create_invoices()
        if lock:
            self.order.action_lock()
        self._return_whole_picking(self.order.picking_ids, to_refund)
        return line_delivery

    def test_auto_refresh_so_and_return_no_invoiced(self):
        """The delivery line is voided as all conditions apply when the return
        is made"""
        line_delivery = self._test_autorefresh_void_line()
        self.assertEqual(line_delivery.price_unit, 0)
        self.assertEqual(line_delivery.product_uom_qty, 0)

    def test_auto_refresh_so_and_return_no_invoiced_locked(self):
        """The delivery line is voided as all conditions apply when the return
        is made. We overrided the locked field in this case"""
        line_delivery = self._test_autorefresh_void_line(lock=True)
        self.assertEqual(line_delivery.price_unit, 0)
        self.assertEqual(line_delivery.product_uom_qty, 0)

    def test_auto_refresh_so_and_return_invoiced(self):
        """There's already an invoice, so the delivery line can't be voided"""
        line_delivery = self._test_autorefresh_void_line(invoice=True)
        self.assertEqual(line_delivery.price_unit, 50)
        self.assertEqual(line_delivery.product_uom_qty, 1)

    def test_auto_refresh_so_and_return_no_refund(self):
        """The return wasn't flagged to refund, so the delivered qty won't
        change, thus the delivery line shouldn't be either"""
        line_delivery = self._test_autorefresh_void_line(to_refund=False)
        self.assertEqual(line_delivery.price_unit, 50)
        self.assertEqual(line_delivery.product_uom_qty, 1)

    def _test_autorefresh_unlink_line(self):
        """Helper method to test the possible cases for voiding the line"""
        self.assertFalse(self.order.order_line.filtered("is_delivery"))
        self.settings.sale_auto_add_delivery_line = True
        self.settings.execute()
        sale_form = Form(self.order)
        # Force the delivery line creation
        with sale_form.order_line.edit(0) as line_form:
            line_form.product_uom_qty = 2
        sale_form.save()
        return self.order.order_line.filtered("is_delivery")

    @mute_logger("odoo.models.unlink")
    def test_auto_refresh_so_and_unlink_line(self):
        """The return wasn't flagged to refund, so the delivered qty won't
        change, thus the delivery line shouldn't be either"""
        self._test_autorefresh_unlink_line()
        delivery_line = self.order.order_line.filtered("is_delivery")
        sale_form = Form(self.order)
        sale_form.order_line.remove(0)
        sale_form.save()
        self.assertFalse(delivery_line.exists())

    def test_auto_add_delivery_line_add_service(self):
        """No delivery line when service only"""
        self.settings.sale_auto_add_delivery_line = True
        self.settings.set_values()
        order_form = Form(self.env["sale.order"])
        order_form.partner_id = self.partner
        with order_form.order_line.new() as ol_form:
            ol_form.product_id = self.service
            ol_form.product_uom_qty = 2
        order = order_form.save()
        delivery_line = order.order_line.filtered("is_delivery")
        self.assertFalse(delivery_line.exists())

    @mute_logger("odoo.models.unlink")
    def test_auto_refresh_so_and_manually_unlink_delivery_line(self):
        """Manually remove the delivery line"""
        delivery_line = self._test_autorefresh_unlink_line()
        sale_form = Form(self.order)
        # Deleting the delivery line
        sale_form.order_line.remove(1)
        sale_form.save()
        self.assertFalse(delivery_line.exists())
