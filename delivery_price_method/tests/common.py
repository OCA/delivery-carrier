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
        self.carrier_free = self.env["delivery.carrier"].create(
            {
                "name": "Free carrier",
                "price_method": "base_on_rule",
                "product_id": product_shipping_cost.id,
                "free_over": True,
                "amount": 0,
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
        self.product_category = self.env["product.category"].create({"name": "Office"})
        self.product = self.env["product.product"].create(
            {
                "name": "Office Chair",
                "categ_id": self.product_category.id,
                "standard_price": 55.0,
                "list_price": 70.0,
                "type": "consu",
                "weight": 0.01,
                "uom_id": self.env.ref("uom.product_uom_unit").id,
                "default_code": "FURN_7777",
                "description_sale": "Comfortable yellow chair for daily work",
            }
        )
        self.res_partner_category = self.env["res.partner.category"].create(
            {"name": "Services", "color": 7}
        )
        self.partner = self.env["res.partner"].create(
            {
                "name": "Azure Interior",
                "category_id": [self.res_partner_category.id],
                "is_company": True,
                "street": "4557 De Silva St",
                "city": "Fremont",
                "state_id": self.env.ref("base.state_us_5").id,
                "zip": "94538",
                "phone": "(870)-931-0505",
                "country_id": self.env.ref("base.us").id,
                "email": "azure.Interior24@example.com",
                "website": "http://www.azure-interior.com",
                "vat": "US12345677",
            }
        )
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
        self.sale_2 = self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "pricelist_id": self.pricelist.id,
                "carrier_id": self.carrier_free.id,
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
        sale_2 = self.sale_2
        delivery_wizard_2 = Form(
            self.env["choose.delivery.carrier"].with_context(
                default_order_id=sale_2.id, default_carrier_id=self.carrier_free
            )
        )
        choose_delivery_carrier_2 = delivery_wizard_2.save()
        choose_delivery_carrier_2.button_confirm()
