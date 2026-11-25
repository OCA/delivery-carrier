# Copyright 2026 Akretion (http://www.akretion.com).
# @author Florian Mounier <florian.mounier@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import Command
from odoo.tests import Form

from odoo.addons.delivery.tests.common import DeliveryCommon
from odoo.addons.sale.tests.common import SaleCommon


class TestDeliveryDiscountedFreeOver(DeliveryCommon, SaleCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._enable_uom()
        cls.product.weight = 1.0
        cls.product_delivery_normal = cls._prepare_carrier_product(
            name="Normal Delivery Charges",
            list_price=10.0,
        )
        cls.normal_delivery = cls._prepare_carrier(
            product=cls.product_delivery_normal,
            name="Normal Delivery Charges",
            delivery_type="fixed",
            fixed_price=100.0,
            free_over=True,
            amount=500.0,
        )

    def test_normal_free_over_behaviour_no_free_over(self):
        so = self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "order_line": [
                    Command.create(
                        {
                            "product_id": self.product.id,
                            "product_uom_qty": 1,
                            "price_unit": 250.00,
                        }
                    )
                ],
            }
        )

        # Add of delivery cost in Sales order
        delivery_wizard = Form(
            self.env["choose.delivery.carrier"].with_context(
                default_order_id=so.id,
                default_carrier_id=self.normal_delivery.id,
            )
        )
        self.assertEqual(
            delivery_wizard.delivery_price,
            100.0,
        )
        delivery_wizard.save().button_confirm()

        line = so.order_line.filtered_domain(
            [("product_id", "=", self.normal_delivery.product_id.id)]
        )
        self.assertEqual(len(line), 1)
        self.assertEqual(line.price_unit, 100.0)
        self.assertEqual(line.product_uom_qty, 1)
        self.assertEqual(line.discount, 0)
        self.assertEqual(line.price_subtotal, 100.0)

    def test_normal_free_over_behaviour_free_over(self):
        so = self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "order_line": [
                    Command.create(
                        {
                            "product_id": self.product.id,
                            "product_uom_qty": 1,
                            "price_unit": 750.00,
                        }
                    )
                ],
            }
        )

        # Add of delivery cost in Sales order
        delivery_wizard = Form(
            self.env["choose.delivery.carrier"].with_context(
                default_order_id=so.id,
                default_carrier_id=self.normal_delivery.id,
            )
        )
        self.assertEqual(
            delivery_wizard.delivery_price,
            0.0,
        )
        delivery_wizard.save().button_confirm()

        line = so.order_line.filtered_domain(
            [("product_id", "=", self.normal_delivery.product_id.id)]
        )
        self.assertEqual(len(line), 1)
        self.assertEqual(line.price_unit, 0.0)
        self.assertEqual(line.product_uom_qty, 1)
        self.assertEqual(line.discount, 0)
        self.assertEqual(line.price_subtotal, 0.0)

    def test_discounted_free_over_behaviour_no_free_over(self):
        self.env.company.free_over_as_discount = True
        so = self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "order_line": [
                    Command.create(
                        {
                            "product_id": self.product.id,
                            "product_uom_qty": 1,
                            "price_unit": 250.00,
                        }
                    )
                ],
            }
        )

        # Add of delivery cost in Sales order
        delivery_wizard = Form(
            self.env["choose.delivery.carrier"].with_context(
                default_order_id=so.id,
                default_carrier_id=self.normal_delivery.id,
            )
        )
        self.assertEqual(
            delivery_wizard.delivery_price,
            100.0,
        )
        delivery_wizard.save().button_confirm()

        line = so.order_line.filtered_domain(
            [("product_id", "=", self.normal_delivery.product_id.id)]
        )
        self.assertEqual(len(line), 1)
        self.assertEqual(line.price_unit, 100.0)
        self.assertEqual(line.product_uom_qty, 1)
        self.assertEqual(line.discount, 0)
        self.assertEqual(line.price_subtotal, 100.0)

    def test_discounted_free_over_behaviour_free_over(self):
        self.env.company.free_over_as_discount = True
        so = self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "order_line": [
                    Command.create(
                        {
                            "product_id": self.product.id,
                            "product_uom_qty": 1,
                            "price_unit": 750.00,
                        }
                    )
                ],
            }
        )

        # Add of delivery cost in Sales order
        delivery_wizard = Form(
            self.env["choose.delivery.carrier"].with_context(
                default_order_id=so.id,
                default_carrier_id=self.normal_delivery.id,
            )
        )
        self.assertEqual(
            delivery_wizard.delivery_price,
            0.0,
        )
        delivery_wizard.save().button_confirm()

        line = so.order_line.filtered_domain(
            [("product_id", "=", self.normal_delivery.product_id.id)]
        )
        self.assertEqual(len(line), 1)
        self.assertEqual(line.price_unit, 100.0)
        self.assertEqual(line.product_uom_qty, 1)
        self.assertEqual(line.discount, 100.0)
        self.assertEqual(line.price_subtotal, 0.0)
