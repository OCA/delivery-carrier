# Copyright 2020 Trey, Kilobytes de Soluciones
# Copyright 2020 Tecnativa - Pedro M. Baeza
# Copyright 2025 Studio73 - Pablo Cortés
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests import Form

from odoo.addons.base.tests.common import BaseCommon


class TestDeliveryPriceMethodCommon(BaseCommon):
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
            }
        )
        self.carrier = self.env["delivery.carrier"].create(
            {
                "name": "Test carrier",
                "delivery_type": "fixed",
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
        self.product = self.env.ref("product.product_delivery_01")
        self.partner = self.env.ref("base.res_partner_12")
        self.sale = self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "pricelist_id": self.pricelist.id,
                "carrier_id": self.carrier.id,
                "order_line": [
                    (0, 0, {"product_id": self.product.id, "product_uom_qty": 1})
                ],
            }
        )

    def _add_delivery(self):
        sale = self.sale
        delivery_wizard = Form(
            self.env["choose.delivery.carrier"].with_context(
                default_order_id=sale.id, default_carrier_id=self.carrier
            )
        )
        choose_delivery_carrier = delivery_wizard.save()
        choose_delivery_carrier.button_confirm()
