# Copyright 2026 Nitrokey GmbH
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests import common


class TestCheckoutLandedCost(common.TransactionCase):
    def test_landed_cost_line_price_total(self):
        """The duties, taxes & fees shown in checkout come from the landed cost
        line ``price_total`` (the value summed in the totals)."""
        product = self.env["product.product"].create(
            {"name": "UPS Duties", "type": "service"}
        )
        partner = self.env["res.partner"].create({"name": "Client"})
        order = self.env["sale.order"].create(
            {
                "partner_id": partner.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": product.id,
                            "product_uom_qty": 1,
                            "price_unit": 25.0,
                            "tax_id": [(6, 0, [])],
                            "is_ups_landed_cost": True,
                        },
                    )
                ],
            }
        )
        landed_cost = sum(
            order.order_line.filtered("is_ups_landed_cost").mapped("price_total")
        )
        self.assertEqual(landed_cost, 25.0)

    def test_landed_cost_line_hidden_from_cart(self):
        """The landed cost line is excluded from the cart display and the cart
        item count."""
        website = self.env["website"].search([], limit=1)
        goods = self.env["product.product"].create(
            {"name": "Goods", "type": "consu", "sale_ok": True}
        )
        tariff = self.env["product.product"].create(
            {"name": "UPS Duties", "type": "service"}
        )
        partner = self.env["res.partner"].create({"name": "Client"})
        order = self.env["sale.order"].create(
            {
                "partner_id": partner.id,
                "website_id": website.id,
                "order_line": [
                    (0, 0, {"product_id": goods.id, "product_uom_qty": 2}),
                    (
                        0,
                        0,
                        {
                            "product_id": tariff.id,
                            "product_uom_qty": 1,
                            "price_unit": 25.0,
                            "is_ups_landed_cost": True,
                        },
                    ),
                ],
            }
        )
        tariff_line = order.order_line.filtered("is_ups_landed_cost")
        self.assertFalse(tariff_line._show_in_cart())
        self.assertNotIn(tariff_line, order.website_order_line)
        self.assertEqual(order.cart_quantity, 2)

    def test_landed_cost_estimate_line_price_total(self):
        """The duties, taxes & fees shown in checkout also include the landed
        cost estimate line ``price_total``."""
        product = self.env["product.product"].create(
            {"name": "UPS Estimated Duties", "type": "service"}
        )
        partner = self.env["res.partner"].create({"name": "Client"})
        order = self.env["sale.order"].create(
            {
                "partner_id": partner.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": product.id,
                            "product_uom_qty": 1,
                            "price_unit": 42.0,
                            "tax_id": [(6, 0, [])],
                            "is_ups_landed_cost_estimate": True,
                        },
                    )
                ],
            }
        )
        landed_cost = sum(
            order.order_line.filtered(
                lambda x: x.is_ups_landed_cost or x.is_ups_landed_cost_estimate
            ).mapped("price_total")
        )
        self.assertEqual(landed_cost, 42.0)

    def test_landed_cost_estimate_line_hidden_from_cart(self):
        """The landed cost estimate line is excluded from the cart display and
        the cart item count."""
        website = self.env["website"].search([], limit=1)
        goods = self.env["product.product"].create(
            {"name": "Goods", "type": "consu", "sale_ok": True}
        )
        tariff = self.env["product.product"].create(
            {"name": "UPS Estimated Duties", "type": "service"}
        )
        partner = self.env["res.partner"].create({"name": "Client"})
        order = self.env["sale.order"].create(
            {
                "partner_id": partner.id,
                "website_id": website.id,
                "order_line": [
                    (0, 0, {"product_id": goods.id, "product_uom_qty": 2}),
                    (
                        0,
                        0,
                        {
                            "product_id": tariff.id,
                            "product_uom_qty": 1,
                            "price_unit": 42.0,
                            "is_ups_landed_cost_estimate": True,
                        },
                    ),
                ],
            }
        )
        tariff_line = order.order_line.filtered("is_ups_landed_cost_estimate")
        self.assertFalse(tariff_line._show_in_cart())
        self.assertNotIn(tariff_line, order.website_order_line)
        self.assertEqual(order.cart_quantity, 2)
