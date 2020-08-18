# Copyright 2020 Camptocamp
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.tests.common import Form, SavepointCase


class TestRoutePutaway(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.partner_18 = cls.env.ref("base.res_partner_18")
        cls.product_4 = cls.env.ref("product.product_product_4")
        cls.product_uom_unit = cls.env.ref("uom.product_uom_unit")
        cls.pricelist = cls.env.ref("product.list0")
        cls.sale_normal_delivery_charges = cls.env["sale.order"].create(
            {
                "partner_id": cls.partner_18.id,
                "partner_invoice_id": cls.partner_18.id,
                "partner_shipping_id": cls.partner_18.id,
                "pricelist_id": cls.pricelist.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "name": "PC Assamble + 2GB RAM",
                            "product_id": cls.product_4.id,
                            "product_uom_qty": 1,
                            "product_uom": cls.product_uom_unit.id,
                            "price_unit": 750.00,
                        },
                    )
                ],
            }
        )
        cls.fee_product = cls.env["product.product"].create(
            {"name": "Fee", "type": "service"}
        )
        cls.carrier_pricelist = cls.env["delivery.carrier"].create(
            {
                "name": "Pricelist Based",
                "delivery_type": "pricelist",
                "product_id": cls.fee_product.id,
            }
        )

    def test_wizard_price(self):
        price = 13.0
        self.env["product.pricelist.item"].create(
            {
                "pricelist_id": self.pricelist.id,
                "product_id": self.fee_product.id,
                "applied_on": "0_product_variant",
                "fixed_price": price,
            }
        )

        delivery_wizard = Form(
            self.env["choose.delivery.carrier"].with_context(
                {"default_order_id": self.sale_normal_delivery_charges.id}
            )
        )
        delivery_wizard.carrier_id = self.carrier_pricelist
        self.assertEqual(delivery_wizard.display_price, price)
