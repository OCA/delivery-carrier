# Copyright 2026 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import Command
from odoo.exceptions import UserError
from odoo.tests import Form
from odoo.tools import mute_logger

from odoo.addons.base.tests.common import BaseCommon


class TestDeliveryOrderSwitchCarrier(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(
            context=dict(cls.env.context, test_delivery_order_switch_carrier=True)
        )
        cls.product = cls.env["product.product"].create(
            {
                "name": "Test Product",
                "type": "consu",
            }
        )
        cls.tax_10 = cls.env["account.tax"].create(
            {
                "name": "Test tax 10%",
                "type_tax_use": "sale",
                "amount": 10,
                "amount_type": "percent",
            }
        )
        cls.tax_15 = cls.env["account.tax"].create(
            {
                "name": "Test tax 15%",
                "type_tax_use": "sale",
                "amount": 15,
                "amount_type": "percent",
            }
        )
        cls.carrier_product_a = cls.env["product.product"].create(
            {
                "name": "Test shipping product A",
                "type": "service",
                "taxes_id": [Command.set(cls.tax_10.ids)],
            }
        )
        cls.carrier_product_b = cls.env["product.product"].create(
            {
                "name": "Test shipping product B",
                "type": "service",
                "taxes_id": [Command.set(cls.tax_10.ids)],
            }
        )
        cls.carrier_a = cls.env["delivery.carrier"].create(
            {
                "name": "Test carrier A",
                "product_id": cls.carrier_product_a.id,
            }
        )
        cls.carrier_b = cls.env["delivery.carrier"].create(
            {
                "name": "Test carrier B",
                "product_id": cls.carrier_product_b.id,
            }
        )
        cls.customer = cls.env["res.partner"].create({"name": "Test customer"})
        cls.sale_order = cls.env["sale.order"].create(
            {
                "partner_id": cls.customer.id,
                "order_line": [
                    Command.create(
                        {
                            "product_id": cls.product.id,
                            "product_uom_qty": 1,
                        }
                    )
                ],
            }
        )

    def _choose_delivery_carrier(self, carrier, delivery_price=False):
        action = self.sale_order.action_open_delivery_wizard()
        wizard_form = Form(
            self.env[action["res_model"]].with_context(**action["context"])
        )
        wizard_form.carrier_id = carrier
        wizard = wizard_form.save()
        if delivery_price:
            # In this way, we assume that the price obtained differs for some other
            # reason; for example, customizations or other scenarios not covered here.
            wizard.delivery_price = delivery_price
        wizard.button_confirm()

    def _get_delivery_line(self):
        return self.sale_order.order_line.filtered(lambda x: x.is_delivery)

    @mute_logger("odoo.models.unlink")
    def test_carrier_change_order(self):
        self.assertFalse(self.sale_order.carrier_id)
        self._choose_delivery_carrier(self.carrier_a)
        self.assertEqual(self.sale_order.carrier_id, self.carrier_a)
        self._choose_delivery_carrier(self.carrier_b)
        self.assertEqual(self.sale_order.carrier_id, self.carrier_b)
        self.sale_order.action_confirm()
        self.assertEqual(self.sale_order.state, "sale")
        self._choose_delivery_carrier(self.carrier_a)
        self.assertEqual(self.sale_order.carrier_id, self.carrier_a)
        delivery_line = self._get_delivery_line()
        self.assertEqual(delivery_line.product_id, self.carrier_product_a)
        self._choose_delivery_carrier(self.carrier_b)
        self.assertEqual(self.sale_order.carrier_id, self.carrier_b)
        delivery_line = self._get_delivery_line()
        self.assertEqual(delivery_line.product_id, self.carrier_product_b)

    def test_carrier_change_order_sale_with_invoice(self):
        self._choose_delivery_carrier(self.carrier_a)
        self.sale_order.action_confirm()
        self.assertEqual(self.sale_order.carrier_id, self.carrier_a)
        delivery_line = self._get_delivery_line()
        delivery_line.price_unit = 10
        self.assertEqual(len(delivery_line), 1)
        self.assertTrue(delivery_line.product_updatable)
        invoice = self.sale_order._create_invoices()
        invoice.action_post()
        self.assertFalse(delivery_line.product_updatable)
        delivery_invoice_line = delivery_line.invoice_lines
        self.assertEqual(invoice.state, "posted")
        self._choose_delivery_carrier(self.carrier_b)
        self.assertEqual(self.sale_order.carrier_id, self.carrier_b)
        self.assertFalse(delivery_line.product_updatable)
        self.assertEqual(delivery_line.product_id, self.carrier_product_b)
        self.assertEqual(delivery_line.name, "Test carrier B")
        self.assertEqual(delivery_invoice_line.product_id, self.carrier_product_b)
        self.assertEqual(delivery_invoice_line.name, "Test carrier B")
        with self.assertRaisesRegex(
            UserError,
            "You can not update the shipping costs on an order where it was already invoiced!",  # noqa: E501
        ):
            self._choose_delivery_carrier(self.carrier_a, 20)

    def test_carrier_change_order_sale_with_invoice_taxes(self):
        self._choose_delivery_carrier(self.carrier_a)
        self.sale_order.action_confirm()
        self.assertEqual(self.sale_order.carrier_id, self.carrier_a)
        delivery_line = self._get_delivery_line()
        delivery_line.price_unit = 10
        delivery_line.tax_id = [Command.set(self.tax_15.ids)]
        self.assertEqual(len(delivery_line), 1)
        self.assertTrue(delivery_line.product_updatable)
        invoice = self.sale_order._create_invoices()
        invoice.action_post()
        self.assertFalse(delivery_line.product_updatable)
        self.assertEqual(invoice.state, "posted")
        with self.assertRaisesRegex(
            UserError,
            "You can not update the shipping costs on an order where it was already invoiced!",  # noqa: E501
        ):
            self._choose_delivery_carrier(self.carrier_b)
