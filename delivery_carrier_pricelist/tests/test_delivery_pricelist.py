# Copyright 2020 Camptocamp
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from lxml import etree

from odoo.tests import Form

from odoo.addons.base.tests.common import BaseCommon


class TestCarrierPricelist(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner_18 = cls.env.ref("base.res_partner_18")
        cls.product_4 = cls.env.ref("product.product_product_4")
        cls.product_uom_unit = cls.env.ref("uom.product_uom_unit")
        cls.pricelist = cls.env["product.pricelist"].create(
            {
                "name": "Public Pricelist",
            }
        )
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

    def create_price_list_item(self):
        price = 13.0
        return self.env["product.pricelist.item"].create(
            {
                "pricelist_id": self.pricelist.id,
                "product_id": self.fee_product.id,
                "applied_on": "0_product_variant",
                "fixed_price": price,
            }
        )

    def get_wiz_form(self, **ctx):
        default_ctx = {"default_order_id": self.sale_normal_delivery_charges.id}
        ctx = {**default_ctx, **ctx}
        return Form(self.env["choose.delivery.carrier"].with_context(**ctx))

    def test_wizard_price(self):
        pl_item = self.create_price_list_item()
        wiz_form = self.get_wiz_form()
        price = pl_item.fixed_price
        saved_carrier = wiz_form.carrier_id
        wiz_form.carrier_id = self.carrier_pricelist
        self.assertEqual(wiz_form.display_price, price)

        wiz_form.carrier_id = saved_carrier
        self.assertEqual(wiz_form.display_price, 0.0)
        self.partner_18.country_id = self.env.ref("base.fr")
        wiz_form.carrier_id = self.carrier_pricelist
        self.assertEqual(wiz_form.display_price, 0.0)

    def test_wizard_invoice_policy(self):
        self.create_price_list_item()
        wiz_form = self.get_wiz_form()
        self.carrier_pricelist.invoice_policy = "pricelist"
        wiz_form.carrier_id = self.carrier_pricelist

    def test_wizard_send_shipping(self):
        pl_item = self.create_price_list_item()
        wiz_form = self.get_wiz_form()
        price = pl_item.fixed_price
        self.carrier_pricelist.invoice_policy = "pricelist"
        wiz_form.carrier_id = self.carrier_pricelist
        rec = wiz_form.save()
        rec.button_confirm()
        so = self.sale_normal_delivery_charges
        so.action_confirm()
        self.assertEqual(so.carrier_id, wiz_form.carrier_id)
        link = wiz_form.carrier_id.get_tracking_link(so.picking_ids)
        self.assertFalse(link)
        result = wiz_form.carrier_id.send_shipping(so.picking_ids)
        expecting = [{"exact_price": price, "tracking_number": False}]
        self.assertEqual(result, expecting)

    def test_fields_view_get(self):
        carrier = self.carrier_pricelist
        result = carrier.get_view()
        doc = etree.XML(result["arch"])
        xpath_expr = "//notebook"
        nodes = doc.xpath(xpath_expr)
        nodes[0].attrib["attrs"] = '{"invisible": 0}'
        carrier._add_pricelist_domain(doc, "//notebook", "invisible")
