# Copyright 2024 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo.tests.common import SavepointCase


class TestDeliveryPurchaseLabel(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        # Mocking to avoid a NotImplementedError
        cls.env["delivery.carrier"]._patch_method(
            "base_on_rule_cancel_shipment", lambda x, y: True
        )
        cls.picking_type = cls.env.ref(
            "delivery_purchase_label.picking_type_send_label"
        )
        cls.supplier = cls.env.ref("base.res_partner_1")
        cls.customer = cls.env.ref("base.res_partner_2")
        cls.carrier = cls.env.ref("delivery.delivery_carrier")
        cls.carrier.purchase_label_picking_type = cls.picking_type

        cls.product = cls.env.ref("product.product_product_5")
        cls.order = cls.env["purchase.order"].create(
            {
                "partner_id": cls.supplier.id,
                "dest_address_id": cls.customer.id,
                "vendor_label_carrier_id": cls.carrier.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "name": cls.product.name,
                            "product_id": cls.product.id,
                            "product_qty": 5.0,
                            "product_uom": cls.product.uom_id.id,
                            "price_unit": 10,
                        },
                    )
                ],
            }
        )
        cls.order.order_line._onchange_quantity()

    def _create_fake_label_attachment(self, linked_to):
        return self.env["ir.attachment"].create(
            {
                "name": "Fake Label Pdf",
                "datas": "bWlncmF0aW9uIHRlc3Q=",
                "res_model": linked_to._name,
                "res_id": linked_to.id,
            }
        )

    def test_transfer_label_generated(self):
        self.order._generate_purchase_delivery_label()
        label_picking = self.order.delivery_label_picking_id
        self.assertEqual(label_picking.picking_type_id, self.picking_type)
        self.assertEqual(label_picking.state, "done")
        # Generating a second time with no changes on the purchase
        # Does not change the picking label
        self.order._generate_purchase_delivery_label()
        self.assertEqual(label_picking, self.order.delivery_label_picking_id)
        self.assertEqual(label_picking.delivery_label_purchase_id, self.order)
        # Changing the PO
        self.order.order_line[0].product_qty = 10
        self.order._generate_purchase_delivery_label()
        self.assertTrue(label_picking.state == "cancel")
        self.assertTrue(label_picking != self.order.delivery_label_picking_id)
        self.assertEqual(
            self.order.delivery_label_picking_id.delivery_label_purchase_id, self.order
        )

    def test_transfer_label_not_generated(self):
        self.carrier.purchase_label_picking_type = False
        self.order._generate_purchase_delivery_label()
        self.assertFalse(self.order.picking_ids)

    def test_add_label_attachment_to_email(self):
        self.order._generate_purchase_delivery_label()
        pdf_label = self._create_fake_label_attachment(
            self.order.delivery_label_picking_id
        )
        vals = {
            "partner_ids": [(6, 0, self.order.partner_id.ids)],
            "model": self.order._name,
            "res_id": self.order.id,
        }
        wiz = self.env["mail.compose.message"].create(vals)
        template = self.env.ref("purchase.email_template_edi_purchase")
        res = wiz.generate_email_for_composer(template.id, self.order.ids, ["subject"])
        self.assertTrue(res[self.order.id].get("attachment_ids"))
        self.assertEqual(res[self.order.id].get("attachment_ids"), pdf_label.ids)

    def test_cancel_purchase_order(self):
        self.order._generate_purchase_delivery_label()
        self.order.button_cancel()
        self.assertTrue(self.order.delivery_label_picking_id.state == "cancel")
