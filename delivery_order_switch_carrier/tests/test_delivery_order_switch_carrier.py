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
        carrier_product = cls.env["product.product"].create(
            {
                "name": "Test shipping product",
                "type": "service",
            }
        )
        cls.carrier_a = cls.env["delivery.carrier"].create(
            {
                "name": "Test carrier A",
                "product_id": carrier_product.id,
            }
        )
        cls.carrier_b = cls.env["delivery.carrier"].create(
            {
                "name": "Test carrier B",
                "product_id": carrier_product.id,
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
        self._choose_delivery_carrier(self.carrier_b)
        self.assertEqual(self.sale_order.carrier_id, self.carrier_b)

    def test_carrier_change_order_sale_with_incoive(self):
        self._choose_delivery_carrier(self.carrier_a)
        self.sale_order.action_confirm()
        self.assertEqual(self.sale_order.carrier_id, self.carrier_a)
        delivery_line = self.sale_order.order_line.filtered("is_delivery")
        delivery_line.price_unit = 10
        self.assertEqual(len(delivery_line), 1)
        invoice = self.sale_order._create_invoices()
        invoice.action_post()
        delivery_invoice_line = delivery_line.invoice_lines
        self.assertEqual(invoice.state, "posted")
        self._choose_delivery_carrier(self.carrier_b)
        self.assertEqual(self.sale_order.carrier_id, self.carrier_b)
        self.assertEqual(delivery_line.name, "Test carrier B")
        self.assertEqual(delivery_invoice_line.name, "Test carrier B")
        with self.assertRaisesRegex(
            UserError,
            "You can not update the shipping costs on an order where it was already invoiced!",  # noqa: E501
        ):
            self._choose_delivery_carrier(self.carrier_a, 20)
