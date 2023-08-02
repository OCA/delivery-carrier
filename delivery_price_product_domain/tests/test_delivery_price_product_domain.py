# Copyright 2023 Cetmix OÜ - Andrey Solodovnikov
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.tests import Form
from odoo.tests.common import SavepointCase
from odoo.tools import float_compare


class TestDeliveryPriceProductDomain(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        self = cls
        product_shipping_cost = self.env["product.product"].create(
            {
                "type": "service",
                "name": "Shipping costs",
                "standard_price": 10,
                "list_price": 100,
                "lst_price": 25,
            }
        )
        self.carrier = self.env["delivery.carrier"].create(
            {
                "name": "Carrier based on rule",
                "delivery_type": "base_on_rule",
                "price_rule_ids": [
                    (
                        0,
                        0,
                        {
                            "variable": "quantity",
                            "operator": "==",
                            "max_value": 2,
                            "list_base_price": 22.22,
                            "apply_product_domain": "[['list_price', '<', 20]]",
                        },
                    )
                ],
                "product_id": product_shipping_cost.id,
                "fixed_price": 99.99,
            }
        )
        self.pricelist = self.env["product.pricelist"].create(
            {
                "name": "Test pricelist",
                "item_ids": [
                    (
                        0,
                        0,
                        {
                            "applied_on": "3_global",
                            "compute_price": "formula",
                            "base": "list_price",
                        },
                    )
                ],
            }
        )
        self.product_delivery_1 = self.env.ref("product.product_delivery_01")
        self.product_delivery_2 = self.env.ref("product.product_delivery_02")
        self.product_service = self.env["product.product"].create(
            {
                "type": "service",
                "name": "Service test",
                "standard_price": 10,
                "list_price": 100,
                "lst_price": 25,
            }
        )
        self.partner = self.env.ref("base.res_partner_12")
        self.sale = self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "pricelist_id": self.pricelist.id,
                "carrier_id": self.carrier.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product_delivery_1.id,
                            "product_uom_qty": 1,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "product_id": self.product_delivery_2.id,
                            "product_uom_qty": 1,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "product_id": self.product_service.id,
                            "product_uom_qty": 1,
                        },
                    ),
                ],
            }
        )

    def _add_delivery(self):
        sale = self.sale
        delivery_wizard = Form(
            self.env["choose.delivery.carrier"].with_context(
                {"default_order_id": sale.id, "default_carrier_id": self.carrier}
            )
        )
        choose_delivery_carrier = delivery_wizard.save()
        choose_delivery_carrier.button_confirm()

    def test_bad_apply_product_domain(self):
        """Test choosing price rule with bad product domain"""
        sale = self.sale
        self._add_delivery()
        delivery_lines = sale.order_line.filtered(lambda r: r.is_delivery)
        delivery_price = sum(delivery_lines.mapped("price_unit"))
        self.assertEqual(
            delivery_price,
            0,
            msg="Must be 0 because none of the product goes throw product domain",
        )
        self.assertEqual(
            len(delivery_lines), 1, msg="Must be 1 because add only 1 shipping"
        )

    def test_apply_product_domain_service(self):
        """Test choosing price rule with product domain"""
        sale = self.sale
        self.carrier.write(
            {
                "price_rule_ids": [
                    (
                        0,
                        0,
                        {
                            "variable": "quantity",
                            "operator": "==",
                            "max_value": 2,
                            "list_base_price": 22.22,
                            "apply_product_domain": "[['type', '!=', 'service']]",
                        },
                    )
                ],
            }
        )
        self._add_delivery()
        delivery_lines = sale.order_line.filtered(lambda r: r.is_delivery)
        delivery_price = sum(delivery_lines.mapped("price_unit"))
        self.assertEqual(
            float_compare(delivery_price, 22.22, precision_digits=2),
            0,
            msg="Must be equal to list_base_price because products go throw product domain",
        )
        self.assertEqual(
            len(delivery_lines), 1, msg="Must be 1 because add only 1 shipping"
        )
