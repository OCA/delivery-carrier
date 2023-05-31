# Copyright 2018-2023 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests import Form, common, tagged


def _execute_onchanges(records, field_name):
    """Helper methods that executes all onchanges associated to a field."""
    for onchange in records._onchange_methods.get(field_name, []):
        for record in records:
            onchange(record)


@tagged("post_install", "-at_install")
class TestDeliveryAutoRefresh(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.env.user.write(
            {
                "groups_id": [
                    (4, cls.env.ref("account.group_delivery_invoice_address").id)
                ]
            }
        )
        service = cls.env["product.product"].create(
            {"name": "Service Test", "type": "service"}
        )
        pricelist = cls.env["product.pricelist"].create(
            {"name": "Test pricelist", "currency_id": cls.env.company.currency_id.id}
        )
        carrier_form = Form(cls.env["delivery.carrier"])
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
        cls.carrier_1 = carrier_form.save()
        carrier_form = Form(cls.env["delivery.carrier"])
        carrier_form.name = "Test carrier 2"
        carrier_form.delivery_type = "base_on_rule"
        carrier_form.product_id = service
        with carrier_form.price_rule_ids.new() as price_rule_form:
            price_rule_form.variable = "weight"
            price_rule_form.operator = "<="
            price_rule_form.max_value = 20
            price_rule_form.list_base_price = 50
        cls.carrier_2 = carrier_form.save()
        cls.product = cls.env["product.product"].create(
            {"name": "Test product", "weight": 10, "list_price": 20}
        )
        cls.partner = cls.env["res.partner"].create(
            {
                "name": "Test partner",
                "property_delivery_carrier_id": cls.carrier_1.id,
                "property_product_pricelist": pricelist.id,
            }
        )
        cls.auto_add_delivery_line = "delivery_auto_refresh.auto_add_delivery_line"
        cls.refresh_after_picking = "delivery_auto_refresh.refresh_after_picking"
        cls.auto_void_delivery_line = "delivery_auto_refresh.auto_void_delivery_line"
        cls.settings = cls.env["res.config.settings"].create({})
        cls.settings.set_default_carrier = True
        cls.settings.execute()
        order_form = Form(cls.env["sale.order"])
        order_form.partner_id = cls.partner
        order_form.partner_invoice_id = cls.partner
        order_form.partner_shipping_id = cls.partner
        with order_form.order_line.new() as ol_form:
            ol_form.product_id = cls.product
            ol_form.product_uom_qty = 2
        cls.order = order_form.save()

    def test_auto_refresh_so(self):
        self.assertFalse(self.order.order_line.filtered("is_delivery"))
        self.settings.auto_add_delivery_line = True
        self.settings.execute()
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
                default_order_id=self.order.id,
                default_carrier_id=self.carrier_1.id,
            )
        ).save()
        wiz.button_confirm()
        self.assertEqual(self.order.carrier_id, self.carrier_1)
        line_delivery = self.order.order_line.filtered("is_delivery")
        self.assertEqual(line_delivery.name, "Test carrier 1")

    def test_auto_refresh_picking(self):
        self.settings.refresh_after_picking = True
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
        picking.move_line_ids[0].qty_done = 2
        picking._action_done()
        line_delivery = self.order.order_line.filtered("is_delivery")
        self.assertEqual(line_delivery.price_unit, 50)

    def test_auto_refresh_picking_fixed_price(self):
        self.settings.refresh_after_picking = True
        self.settings.execute()
        product_fixed_price = self.env["product.product"].create(
            {
                "name": "Test carrier fixed price auto refresh",
                "type": "service",
            }
        )
        carrier_form = Form(self.env["delivery.carrier"])
        carrier_form.name = product_fixed_price.name
        carrier_form.product_id = product_fixed_price
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
        self.order.action_done()  # Lock order to check writing protection disabling
        picking = self.order.picking_ids
        picking.action_assign()
        picking.move_line_ids[0].qty_done = 2
        picking._action_done()
        line_delivery = self.order.order_line.filtered("is_delivery")
        self.assertEqual(line_delivery.price_unit, 2)

    def test_no_auto_refresh_picking(self):
        self.settings.refresh_after_picking = False
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
            line.quantity_done = line.product_uom_qty
        picking._action_done()

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
        return_wiz.product_return_moves.quantity = picking.move_ids.quantity_done
        return_wiz.product_return_moves.to_refund = to_refund
        res = return_wiz.create_returns()
        return_picking = self.env["stock.picking"].browse(res["res_id"])
        self._validate_picking(return_picking)

    def _test_autorefresh_void_line(self, lock=False, to_refund=True, invoice=False):
        """Helper method to test the possible cases for voiding the line"""
        self.assertFalse(self.order.order_line.filtered("is_delivery"))
        self.settings.auto_add_delivery_line = True
        self.settings.auto_void_delivery_line = True
        self.settings.execute()
        line_delivery = self._confirm_sale_order(self.order)
        self._validate_picking(self.order.picking_ids)
        if invoice:
            self.order._create_invoices()
        if lock:
            self.order.action_done()
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
        is made. We overrided the locked state in this case"""
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
        self.settings.auto_add_delivery_line = True
        self.settings.execute()
        sale_form = Form(self.order)
        # Force the delivery line creation
        with sale_form.order_line.edit(0) as line_form:
            line_form.product_uom_qty = 2
        sale_form.save()
        return self.order.order_line.filtered("is_delivery")

    def test_auto_refresh_so_and_unlink_line(self):
        """The return wasn't flagged to refund, so the delivered qty won't
        change, thus the delivery line shouldn't be either"""
        self._test_autorefresh_unlink_line()
        delivery_line = self.order.order_line.filtered("is_delivery")
        sale_form = Form(self.order)
        sale_form.order_line.remove(0)
        sale_form.save()
        self.assertFalse(delivery_line.exists())
