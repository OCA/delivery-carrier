# Copyright 2019 Tecnativa - Vicent Cubells
# Copyright 2022 Tecnativa - Víctor Martínez
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo.tests.common import TransactionCase


class TestDeliveryFreeFeeRemoval(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        product = cls.env["product.product"].create(
            {"name": "Product", "detailed_type": "product"}
        )
        product_delivery = cls.env["product.product"].create(
            {
                "name": "Delivery Product",
                "detailed_type": "service",
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
        partner = cls.env["res.partner"].create({"name": "Test Partner"})
        cls.sale = cls.env["sale.order"].create(
            {
                "partner_id": partner.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": product.id,
                            "product_uom_qty": 1,
                            "product_uom": product.uom_id.id,
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
        res = self.report_obj._get_report_from_name(
            "sale.report_saleorder"
        )._render_qweb_text(self.sale.ids, False)
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
        res = self.report_obj._get_report_from_name(
            "sale.report_saleorder"
        )._render_qweb_text(self.sale.ids, False)
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
        res = self.report_obj._get_report_from_name(
            "sale.report_saleorder"
        )._render_qweb_text(self.sale.ids, False)
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
        res = self.report_obj._get_report_from_name(
            "sale.report_saleorder"
        )._render_qweb_text(self.sale.ids, False)
        self.assertNotRegex(str(res[0]), "Test Delivery")
