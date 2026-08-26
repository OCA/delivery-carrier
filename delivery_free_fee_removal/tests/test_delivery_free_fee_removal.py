# Copyright 2019 Tecnativa - Vicent Cubells
# Copyright 2022 Tecnativa - Víctor Martínez
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo.orm.commands import Command
from odoo.tests import Form
from odoo.tools import mute_logger

from odoo.addons.base.tests.common import BaseCommon


class TestDeliveryFreeFeeRemoval(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        product = cls.env["product.product"].create(
            {"name": "Product", "type": "consu"}
        )
        product_delivery = cls.env["product.product"].create(
            {
                "name": "Delivery Product",
                "type": "service",
                "invoice_policy": "delivery",
            }
        )
        cls.delivery = cls.env["delivery.carrier"].create(
            {
                "name": "Test Delivery",
                "delivery_type": "fixed",
                "fixed_price": 10,
                "free_over": True,
                "product_id": product_delivery.id,
            }
        )
        cls.sale = cls.env["sale.order"].create(
            {
                "partner_id": cls.partner.id,
                "order_line": [
                    Command.create(
                        {
                            "product_id": product.id,
                            "product_uom_qty": 1,
                            "product_uom_id": product.uom_id.id,
                            "price_unit": 3.0,
                        },
                    )
                ],
            }
        )
        cls.report_obj = cls.env["ir.actions.report"]

    def test_delivery_free_fee_removal_with_fee(self):
        self.delivery.product_id.write({"invoice_policy": "order"})
        self.sale.set_delivery_line(self.delivery, 100)
        delivery_line = self.sale.mapped("order_line").filtered(lambda x: x.is_delivery)
        self.assertFalse(delivery_line.is_free_delivery)
        self.sale.action_confirm()
        self.assertRecordValues(
            delivery_line,
            [
                {
                    "is_free_delivery": False,
                    "qty_to_invoice": 1,
                    "invoice_status": "to invoice",
                }
            ],
        )
        report = self.report_obj._get_report_from_name("sale.report_saleorder")
        res = report._render_qweb_text(report, self.sale.ids, False)
        self.assertRegex(str(res[0]), "Test Delivery")

    def test_delivery_free_fee_removal_with_fee_invoice_policy_delivery(self):
        self.sale.set_delivery_line(self.delivery, 100)
        delivery_line = self.sale.mapped("order_line").filtered(lambda x: x.is_delivery)
        self.assertFalse(delivery_line.is_free_delivery)
        self.sale.action_confirm()
        self.assertRecordValues(
            delivery_line,
            [
                {
                    "is_free_delivery": False,
                    "qty_to_invoice": 0,
                    # SO not yet delivered so nothing to invoice
                    "invoice_status": "no",
                }
            ],
        )
        report = self.report_obj._get_report_from_name("sale.report_saleorder")
        res = report._render_qweb_text(report, self.sale.ids, False)
        self.assertRegex(str(res[0]), "Test Delivery")

    def test_delivery_free_fee_removal_free_fee(self):
        self.sale.set_delivery_line(self.delivery, 0)
        delivery_line = self.sale.mapped("order_line").filtered(lambda x: x.is_delivery)
        self.assertTrue(delivery_line.is_free_delivery)
        self.sale.action_confirm()
        self.assertRecordValues(
            delivery_line,
            [
                {
                    "is_free_delivery": True,
                    "qty_to_invoice": 0,
                    "invoice_status": "invoiced",
                }
            ],
        )
        report = self.report_obj._get_report_from_name("sale.report_saleorder")
        res = report._render_qweb_text(report, self.sale.ids, False)
        self.assertNotRegex(str(res[0]), "Test Delivery")

    def test_delivery_free_fee_removal_free_fee_invoice_policy_order(self):
        self.delivery.product_id.write({"invoice_policy": "order"})
        self.sale.set_delivery_line(self.delivery, 0)
        delivery_line = self.sale.mapped("order_line").filtered(lambda x: x.is_delivery)
        self.assertTrue(delivery_line.is_free_delivery)
        self.sale.action_confirm()
        self.assertRecordValues(
            delivery_line,
            [
                {
                    "is_free_delivery": True,
                    "qty_to_invoice": 0,
                    "invoice_status": "invoiced",
                }
            ],
        )
        report = self.report_obj._get_report_from_name("sale.report_saleorder")
        res = report._render_qweb_text(report, self.sale.ids, False)
        self.assertNotRegex(str(res[0]), "Test Delivery")

    def _set_delivery_carrier(self, carrier):
        form = Form(
            self.env["choose.delivery.carrier"].with_context(
                default_order_id=self.sale.id,
            ),
            view="delivery.choose_delivery_carrier_view_form",
        )
        form.carrier_id = carrier
        shipping = form.save()
        shipping.button_confirm()

    @mute_logger("odoo.models.unlink")
    def test_update_carrier_after_so_confirm(self):
        self.delivery.fixed_price = 0
        self._set_delivery_carrier(self.delivery)
        self.sale.action_confirm()
        other_carrier = self.env["delivery.carrier"].create(
            {
                "name": "Other Delivery (delivery_free_fee_removal)",
                "delivery_type": "fixed",
                "fixed_price": 10,
                "free_over": True,
                "product_id": self.delivery.product_id.id,
            }
        )
        self._set_delivery_carrier(other_carrier)  # This shouldn't fail
