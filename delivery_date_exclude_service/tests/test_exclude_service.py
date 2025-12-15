# Copyright 2025 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import timedelta

from odoo import fields
from odoo.tests import Form
from odoo.tests.common import TransactionCase
from odoo.tools import mute_logger


class TestExcludeService(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.today = fields.Date.today()
        cls.product1 = cls.env["product.product"].create(
            {
                "name": "Product 1",
                "type": "consu",
                "is_storable": True,
                "lst_price": 1.0,
                "sale_delay": 5.0,  # 5 day lead time
            }
        )
        cls.service1 = cls.env["product.product"].create(
            {
                "name": "Shipping",
                "type": "service",
                "sale_delay": 2.0,  # 2 day lead time (should be ignored)
                # "service_affect_delivery_date": False by default
            }
        )
        cls.service_affect_delivery_date = cls.env["product.product"].create(
            {
                "name": "Affect Delivery",
                "type": "service",
                "sale_delay": 3.0,  # 3 day lead time (should be considered)
                "service_affect_delivery_date": True,
            }
        )
        cls.partner = cls.env["res.partner"].create({"name": "Partner"})

    @classmethod
    def _create_sale(cls, products):
        sale_form = Form(cls.env["sale.order"])
        sale_form.partner_id = cls.partner
        with mute_logger("odoo.tests.common.onchange"):
            for product in products:
                with sale_form.order_line.new() as line:
                    line.product_id = product
                    line.product_uom_qty = 1.0
        return sale_form.save()

    def test_expected_delivery_date_exclusion(self):
        self.sale = self._create_sale([self.product1, self.service1])
        self.sale.action_confirm()
        expected_date = self.today + timedelta(days=5)
        self.assertEqual(
            self.sale.expected_date.date(),
            expected_date,
            "Expected date should be driven by the 5-day product line only.",
        )

    def test_expected_delivery_date_inclusion(self):
        self.sale = self._create_sale(
            [self.product1, self.service_affect_delivery_date]
        )
        self.sale.action_confirm()
        expected_date = self.today + timedelta(days=3)
        self.assertEqual(
            self.sale.expected_date.date(),
            expected_date,
            "Expected date should be driven by the 3-day service line "
            "as the shortest lead time is considered.",
        )

    def test_expected_delivery_date_no_dates(self):
        # Add only the Service W/O Flag (service1)
        self.sale = self._create_sale([self.service1])
        self.sale.action_confirm()

        self.assertEqual(
            self.sale.expected_date,
            False,
            "The commitment date must be False when all contributing lines "
            "are excluded from date calculation.",
        )
