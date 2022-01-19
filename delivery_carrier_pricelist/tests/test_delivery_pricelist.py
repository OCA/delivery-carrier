# Copyright 2020 Camptocamp
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from lxml import etree

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
                "country_ids": [(6, 0, [cls.partner_18.country_id.id])],
            }
        )

    def create_price_list(self):
        price = 13.0
        self.pricelist_item = self.env["product.pricelist.item"].create(
            {
                "pricelist_id": self.pricelist.id,
                "product_id": self.fee_product.id,
                "applied_on": "0_product_variant",
                "fixed_price": price,
            }
        )

    def create_wizard(self):
        self.delivery_wizard = Form(
            self.env["choose.delivery.carrier"].with_context(
                {"default_order_id": self.sale_normal_delivery_charges.id}
            )
        )

    def test_wizard_price(self):
        self.create_price_list()
        self.create_wizard()
        price = self.pricelist_item.fixed_price
        delivery_wizard = self.delivery_wizard
        saved_carrier = delivery_wizard.carrier_id
        delivery_wizard.carrier_id = self.carrier_pricelist
        self.assertEqual(delivery_wizard.display_price, price)

        delivery_wizard.carrier_id = saved_carrier
        self.assertEqual(delivery_wizard.display_price, 0.0)
        self.partner_18.country_id = self.env.ref("base.fr")
        delivery_wizard.carrier_id = self.carrier_pricelist
        self.assertEqual(delivery_wizard.display_price, 0.0)

    def test_wizard_invoice_policy(self):
        self.create_price_list()
        self.create_wizard()
        delivery_wizard = self.delivery_wizard

        self.carrier_pricelist.invoice_policy = "pricelist"
        delivery_wizard.carrier_id = self.carrier_pricelist

    def test_wizard_send_shipping(self):
        self.create_price_list()
        self.create_wizard()
        price = self.pricelist_item.fixed_price
        self.carrier_pricelist.invoice_policy = "pricelist"
        delivery_wizard = self.delivery_wizard
        delivery_wizard.carrier_id = self.carrier_pricelist
        rec = delivery_wizard.save()
        rec.button_confirm()
        so = self.sale_normal_delivery_charges
        so.action_confirm()
        self.assertEqual(so.carrier_id, delivery_wizard.carrier_id)
        link = delivery_wizard.carrier_id.get_tracking_link(so.picking_ids)
        self.assertFalse(link)
        result = delivery_wizard.carrier_id.send_shipping(so.picking_ids)
        expecting = [{"exact_price": price, "tracking_number": False}]
        self.assertEqual(result, expecting)

    def test_fields_view_get(self):
        carrier = self.carrier_pricelist
        result = carrier.fields_view_get()
        doc = etree.XML(result["arch"])
        xpath_expr = "//notebook"
        nodes = doc.xpath(xpath_expr)
        nodes[0].attrib["attrs"] = '{"invisible": 0}'
        carrier._add_pricelist_domain(doc, "//notebook", "invisible")
