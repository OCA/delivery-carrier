# Copyright 2026 Moduon
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
from odoo import Command
from odoo.tests import Form, TransactionCase


class DeliveryFeeTestCase(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.delivery_product = cls.env["product.product"].create(
            {
                "name": "Delivery test",
                "type": "service",
                "list_price": 5.0,
            }
        )
        cls.fee_product = cls.env["product.product"].create(
            {
                "name": "Delivery Fee Test",
                "type": "service",
                "list_price": 2.0,
                "description_sale": "Delivery fee charged per shipment",
            }
        )
        cls.carrier_with_fee = cls.env["delivery.carrier"].create(
            {
                "name": "Carrier with Fee",
                "delivery_type": "fixed",
                "product_id": cls.delivery_product.id,
                "fixed_price": 5.0,
                "fee_product_id": cls.fee_product.id,
                "fee_return_percentage": 75,
            }
        )
        cls.carrier_without_fee = cls.env["delivery.carrier"].create(
            {
                "name": "Carrier without Fee",
                "delivery_type": "fixed",
                "product_id": cls.delivery_product.id,
                "fixed_price": 5.0,
            }
        )
        cls.product = cls.env["product.product"].create(
            {
                "name": "Test Product",
                "type": "consu",
                "list_price": 100.0,
            }
        )
        cls.customer = cls.env["res.partner"].create({"name": "Mr. Odoo"})
        cls.exempt_customer = cls.env["res.partner"].create(
            {
                "name": "Mrs. Exempted",
                "delivery_fee_exemption": True,
            }
        )
        cls.sale_order = cls.env["sale.order"].create(
            {
                "partner_id": cls.customer.id,
                "order_line": [
                    Command.create(
                        {
                            "product_id": cls.product.id,
                            "product_uom_qty": 1,
                            "price_unit": 100.0,
                        }
                    ),
                ],
            }
        )
        # Defaults to `False`, but it's useful to declare it explicitly for local tests
        cls.env.company.one_delivery_fee_by_sale_order = False

    def _validate_picking(self, picking):
        picking.action_set_quantities_to_reservation()
        picking._action_done()

    def _picking_return(self, picking, qty=None):
        stock_return_picking_form = Form(
            self.env["stock.return.picking"].with_context(
                active_ids=picking.ids,
                active_id=picking.id,
                active_model="stock.picking",
            )
        )
        stock_return_picking = stock_return_picking_form.save()
        if qty:
            stock_return_picking.product_return_moves.quantity = qty
        stock_return_picking_action = stock_return_picking.create_returns()
        return_pick = self.env["stock.picking"].browse(
            stock_return_picking_action["res_id"]
        )
        self._validate_picking(return_pick)
        return return_pick

    def _add_line_to_sale_order(self, sale):
        so_form = Form(self.sale_order)
        with so_form.order_line.new() as line:
            line.product_id = self.product
        so_form.save()

    def _test_regex_in_report(self, report, res_ids, expression, expected_in_html=True):
        """Helper method to test whether or not a regular expression should be
        expected in the report resulting rendering"""
        html, _ = self.env["ir.actions.report"]._render_qweb_html(report, res_ids)
        assertion = self.assertRegex if expected_in_html else self.assertNotRegex
        assertion(str(html), expression)

    def _common_test_delivery_fee_added_on_picking_validation(self):
        self.sale_order.carrier_id = self.carrier_with_fee
        self.sale_order.action_confirm()
        picking = self.sale_order.picking_ids
        self._validate_picking(picking)
        fee_lines = self.sale_order.order_line.filtered("is_delivery_fee")
        self.assertEqual(len(fee_lines), 1)
        self.assertEqual(fee_lines.price_unit, 2.0)
        # The fee text is printed
        self._test_regex_in_report(
            "stock.report_deliveryslip",
            picking.ids,
            r"Delivery fee charged per shipment.+2",
        )

    def _common_fee_added_on_picking_validation_refund(self):
        """"""
        picking_2, picking_1 = self.sale_order.picking_ids
        return_pick_1 = self._picking_return(picking_1)
        # The fee shouldn't show up in returns
        self._test_regex_in_report(
            "stock.report_deliveryslip",
            return_pick_1.ids,
            r"Delivery fee charged per shipment",
            expected_in_html=False,
        )
        self.assertFalse(self.sale_order.all_fee_pickings_returned)
        picking_1_fee = self.sale_order.order_line.filtered(
            lambda x, pick=picking_1: x.is_delivery_fee
            and x.delivery_fee_picking_id == pick
        )
        self.assertAlmostEqual(picking_1_fee.price_subtotal, 2)
        self.assertAlmostEqual(picking_1_fee.product_uom_qty, 1)
        return_pick_2 = self._picking_return(picking_2)
        self._test_regex_in_report(
            "stock.report_deliveryslip",
            return_pick_2.ids,
            r"Delivery fee charged per shipment",
            expected_in_html=False,
        )
        self.assertTrue(self.sale_order.all_fee_pickings_returned)
        self.assertAlmostEqual(picking_1_fee.price_subtotal, 0.50)
        self.assertAlmostEqual(picking_1_fee.product_uom_qty, 0.25)

    def test_delivery_fee_added_on_picking_validation(self):
        """Test that delivery fee is added when picking is validated"""
        self._common_test_delivery_fee_added_on_picking_validation()
        existing_picking = self.sale_order.picking_ids
        # Let's add a new picking
        self._add_line_to_sale_order(self.sale_order)
        new_picking = self.sale_order.picking_ids - existing_picking
        self._validate_picking(new_picking)
        fee_lines = self.sale_order.order_line.filtered("is_delivery_fee")
        self.assertEqual(len(fee_lines), 2)
        self._test_regex_in_report(
            "stock.report_deliveryslip",
            new_picking.ids,
            r"Delivery fee charged per shipment.+2",
        )
        # The fee is printed in the invoice report as well
        invoice = self.sale_order._create_invoices()
        self._test_regex_in_report(
            "account.report_invoice",
            invoice.ids,
            r"Delivery fee charged per shipment.+2",
        )
        self._common_fee_added_on_picking_validation_refund()

    def test_delivery_fee_added_on_picking_validation_one_fee_per_order(self):
        """Same tests as before, but now only one fee is added when the first
        picking is validated"""
        self.env.company.one_delivery_fee_by_sale_order = True
        self._common_test_delivery_fee_added_on_picking_validation()
        existing_picking = self.sale_order.picking_ids
        # Let's add a new picking
        self._add_line_to_sale_order(self.sale_order)
        new_picking = self.sale_order.picking_ids - existing_picking
        self._validate_picking(new_picking)
        fee_lines = self.sale_order.order_line.filtered("is_delivery_fee")
        self.assertEqual(len(fee_lines), 1, "The fee should be added just once!")
        self._test_regex_in_report(
            "stock.report_deliveryslip",
            new_picking.ids,
            r"Delivery fee charged per shipment",
            expected_in_html=False,
        )
        # The fee is printed in the invoice report as well
        invoice = self.sale_order._create_invoices()
        self._test_regex_in_report(
            "account.report_invoice",
            invoice.ids,
            r"Delivery fee charged per shipment.+2",
        )
        self._common_fee_added_on_picking_validation_refund()

    def test_no_fee_for_carrier_without_fee_product(self):
        """Test that no fee is added if carrier has no fee product"""
        self.sale_order.carrier_id = self.carrier_without_fee
        self.sale_order.action_confirm()
        picking = self.sale_order.picking_ids
        self._validate_picking(picking)
        fee_lines = self.sale_order.order_line.filtered("is_delivery_fee")
        self.assertEqual(len(fee_lines), 0)
        self._test_regex_in_report(
            "stock.report_deliveryslip",
            picking.ids,
            r"Delivery fee charged per shipment",
            expected_in_html=False,
        )

    def test_exempt_customer_no_fee(self):
        """Test that exempt customers don't get charged delivery fees"""
        so_form = Form(self.sale_order)
        so_form.partner_id = self.exempt_customer
        so_form.save()
        self.sale_order.carrier_id = self.carrier_with_fee
        self.sale_order.action_confirm()
        picking = self.sale_order.picking_ids
        self._validate_picking(picking)
        fee_lines = self.sale_order.order_line.filtered("is_delivery_fee")
        self.assertEqual(len(fee_lines), 0)
        self._test_regex_in_report(
            "stock.report_deliveryslip",
            picking.ids,
            r"Delivery fee charged per shipment",
            expected_in_html=False,
        )
