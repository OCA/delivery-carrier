# Copyright 2020 Trey, Kilobytes de Soluciones
# Copyright 2020 FactorLibre
# Copyright 2022 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields
from odoo.tests import Form
from odoo.tests.common import TransactionCase
from odoo.tools import float_compare


class TestDeliveryState(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        product_shipping_cost = cls.env["product.product"].create(
            {
                "type": "service",
                "name": "Shipping costs",
                "standard_price": 10,
                "list_price": 100,
            }
        )
        cls.carrier = cls.env["delivery.carrier"].create(
            {
                "name": "Test carrier",
                "delivery_type": "fixed",
                "product_id": product_shipping_cost.id,
                "fixed_price": 99.99,
            }
        )
        cls.product = cls.env["product.product"].create(
            {"name": "Test product", "type": "product"}
        )
        cls.partner = cls.env["res.partner"].create({"name": "Mr. Odoo"})
        cls.partner_shipping = cls.env["res.partner"].create(
            {"name": "Mr. Odoo (shipping)", "email": "test@test.com"}
        )
        cls.pricelist = cls.env["product.pricelist"].create(
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
        cls.sale = cls.env["sale.order"].create(
            {
                "partner_id": cls.partner.id,
                "partner_shipping_id": cls.partner_shipping.id,
                "pricelist_id": cls.pricelist.id,
                "order_line": [
                    (0, 0, {"product_id": cls.product.id, "product_uom_qty": 1})
                ],
            }
        )

    def test_delivery_state(self):
        delivery_wizard = Form(
            self.env["choose.delivery.carrier"].with_context(
                **{"default_order_id": self.sale.id, "default_carrier_id": self.carrier}
            )
        )
        choose_delivery_carrier = delivery_wizard.save()
        choose_delivery_carrier.button_confirm()
        delivery_lines = self.sale.order_line.filtered(lambda r: r.is_delivery)
        delivery_price = sum(delivery_lines.mapped("price_unit"))
        self.assertEqual(float_compare(delivery_price, 99.99, precision_digits=2), 0)
        self.assertEqual(len(delivery_lines), 1)
        self.sale.action_confirm()
        picking = self.sale.picking_ids[0]
        self.assertEqual(len(picking.move_lines), 1)
        self.assertEqual(picking.carrier_id, self.carrier)
        picking.action_confirm()
        picking.action_assign()
        picking.send_to_shipper()
        self.assertEqual(picking.delivery_state, "shipping_recorded_in_carrier")
        self.assertTrue(picking.date_shipped)
        self.assertFalse(picking.tracking_state_history)
        picking.tracking_state_update()
        picking.date_delivered = fields.Datetime.now()
        with self.assertRaises(NotImplementedError):
            picking.cancel_shipment()
        self.env["delivery.carrier"]._patch_method(
            "fixed_cancel_shipment", lambda *args: True
        )
        picking.cancel_shipment()
        self.assertEqual(picking.delivery_state, "canceled_shipment")
        self.assertFalse(picking.date_shipped)
        self.assertFalse(picking.date_delivered)

    def test_delivery_confirmation_send(self):
        template = self.env.ref("delivery_state.delivery_state_delivered_notification")
        template.auto_delete = False
        self.sale.action_confirm()
        picking = self.sale.picking_ids
        picking.company_id.delivery_state_delivered_email_validation = True
        picking.company_id.delivery_state_delivered_mail_template_id = template
        picking.carrier_tracking_ref = "XX-0000"
        picking.move_lines.quantity_done = 1
        picking._action_done()
        picking.write({"delivery_state": "customer_delivered"})
        mails = picking.message_ids.filtered(
            lambda x: self.partner_shipping in x.partner_ids
        )
        last_mail = fields.first(mails)
        self.assertTrue("XX-0000" in last_mail.body)
