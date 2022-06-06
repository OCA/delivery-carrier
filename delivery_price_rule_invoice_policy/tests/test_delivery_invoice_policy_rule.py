# Copyright 2022 Studio73 - Ethan Hildick <ethan@studio73.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import Form, SavepointCase


class TestDeliveryInvoicePolicyRule(SavepointCase):
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
        cls.carrier = cls.env["delivery.carrier"].create(
            {
                "name": "Pricelist Based",
                "delivery_type": "fixed",
                "invoice_policy": "base_on_rule",
                "product_id": cls.fee_product.id,
                "country_ids": [(6, 0, [cls.partner_18.country_id.id])],
                "price_rule_ids": [
                    (
                        0,
                        0,
                        {
                            "variable": "price",
                            "operator": ">",
                            "max_value": 0,
                            "list_base_price": 50,
                            "list_price": 0,
                            "variable_factor": "price",
                        },
                    )
                ],
            }
        )

    def create_wizard(self):
        self.delivery_wizard = Form(
            self.env["choose.delivery.carrier"].with_context(
                {"default_order_id": self.sale_normal_delivery_charges.id}
            )
        )

    def test_wizard_send_shipping(self):
        self.create_wizard()
        delivery_wizard = self.delivery_wizard
        delivery_wizard.carrier_id = self.carrier
        rec = delivery_wizard.save()
        rec.button_confirm()
        so = self.sale_normal_delivery_charges
        so.action_confirm()
        self.assertEqual(so.carrier_id, delivery_wizard.carrier_id)
        result = delivery_wizard.carrier_id.send_shipping(so.picking_ids)
        expecting = [{"exact_price": 50, "tracking_number": False}]
        self.assertEqual(result, expecting)
