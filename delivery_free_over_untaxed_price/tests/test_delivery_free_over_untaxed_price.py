# Copyright 2025 Alberto Martínez <alberto.martinez@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command

from odoo.addons.delivery.tests.common import DeliveryCommon


class TestDeliveryFreeOverUntaxedPrice(DeliveryCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        delivery_product = cls._prepare_carrier_product()
        cls.product = cls.env["product.product"].create({"name": "Test Product"})
        cls.partner = cls.env["res.partner"].create({"name": "Test Partner"})
        cls.delivery_free_untaxed = cls._prepare_carrier(
            product=delivery_product,
            name="Delivery Free Untaxed",
            free_over=True,
            amount=100,
            use_amount_untaxed=True,
        )
        cls.delivery_free_taxed = cls._prepare_carrier(
            product=delivery_product,
            name="Delivery Free Untaxed",
            free_over=True,
            amount=100,
            use_amount_untaxed=False,
        )
        cls.tax = cls.env["account.tax"].create(
            {
                "name": "Test tax",
                "amount_type": "percent",
                "amount": 10,
            }
        )
        cls.sale1 = cls.env["sale.order"].create(
            {
                "partner_id": cls.partner.id,
                "partner_invoice_id": cls.partner.id,
                "partner_shipping_id": cls.partner.id,
                "order_line": [
                    Command.create(
                        {
                            "product_id": cls.product.id,
                            "price_unit": 99.99,
                            "tax_id": [(6, 0, [cls.tax.id])],
                        }
                    )
                ],
            }
        )
        cls.sale2 = cls.env["sale.order"].create(
            {
                "partner_id": cls.partner.id,
                "partner_invoice_id": cls.partner.id,
                "partner_shipping_id": cls.partner.id,
                "order_line": [
                    Command.create(
                        {
                            "product_id": cls.product.id,
                            "price_unit": 100.00,
                        }
                    )
                ],
            }
        )

    def test_rate_shipments(self):
        res = self.delivery_free_untaxed.rate_shipment(self.sale1)
        self.assertFalse(res["warning_message"])
        self.assertTrue(res["price"])

        res = self.delivery_free_taxed.rate_shipment(self.sale1)
        self.assertTrue(res["warning_message"])
        self.assertFalse(res["price"])

        res = self.delivery_free_untaxed.rate_shipment(self.sale2)
        self.assertTrue(res["warning_message"])
        self.assertFalse(res["price"])
