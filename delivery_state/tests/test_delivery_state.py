# Copyright 2020 Trey, Kilobytes de Soluciones
# Copyright 2020 FactorLibre
# Copyright 2022 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from unittest.mock import patch

from odoo import fields
from odoo.tests import Form
from odoo.tests.common import TransactionCase
from odoo.tools import float_compare
from odoo.tools.binary import BinaryBytes


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
            {"name": "Test product", "type": "consu"}
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
                            "compute_price": "discount",
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
        cls.picking = cls.env["stock.picking"].create(
            {
                "picking_type_id": cls.env["stock.picking.type"].search([], limit=1).id,
                "partner_id": cls.partner.id,
                "location_id": cls.env["stock.location"]
                .search([("usage", "=", "internal")], limit=1)
                .id,
                "location_dest_id": cls.env["stock.location"]
                .search([("usage", "=", "customer")], limit=1)
                .id,
                "move_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": cls.product.id,
                            "product_uom_qty": 1,
                            "uom_id": cls.product.uom_id.id,
                            "location_id": cls.env["stock.location"]
                            .search([("usage", "=", "internal")], limit=1)
                            .id,
                            "location_dest_id": cls.env["stock.location"]
                            .search([("usage", "=", "customer")], limit=1)
                            .id,
                        },
                    )
                ],
            }
        )

    def test_delivery_state(self):
        delivery_wizard = Form(
            self.env["choose.delivery.carrier"].with_context(
                default_order_id=self.sale.id, default_carrier_id=self.carrier
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
        self.assertEqual(len(picking.move_ids), 1)
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
        self.assertEqual(picking.delivery_state, "shipping_recorded_in_carrier")
        with patch.object(
            self.env["delivery.carrier"].__class__,
            "fixed_cancel_shipment",
            return_value=True,
        ) as cancel:
            picking.cancel_shipment()
            cancel.assert_called_once_with(picking)
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
        picking.move_ids.quantity = 1
        picking._action_done()
        picking.write({"delivery_state": "customer_delivered"})
        mails = picking.message_ids.filtered(
            lambda x: self.partner_shipping in x.partner_ids
        )
        last_mail = next(iter(mails))
        self.assertTrue("XX-0000" in last_mail.body)

    def test_update_delivery_state(self):
        carrier = self.carrier.copy({"delivery_type": "base_on_rule"})
        self.picking.write({"carrier_id": carrier.id, "state": "done"})
        terminal = self.env["stock.picking"]
        for state in ("customer_delivered", "canceled_shipment", "no_update"):
            picking = self.picking.copy({"carrier_id": carrier.id})
            picking.write({"state": "done", "delivery_state": state})
            terminal |= picking
        pending = self.picking.copy({"carrier_id": carrier.id})
        self.picking.delivery_state = "shipping_recorded_in_carrier"
        with patch.object(
            type(self.picking), "tracking_state_update", autospec=True
        ) as update:
            self.env["stock.picking"]._update_delivery_state()
            selected = update.call_args.args[0]
            self.assertIn(self.picking, selected)
            self.assertFalse(terminal & selected)
            self.assertNotIn(pending, selected)

    def test_tracking_adapter_error_and_cron(self):
        self.picking.carrier_id = self.carrier
        other = self.picking.copy({"carrier_id": self.carrier.id})

        def update(carrier, picking):
            picking.tracking_state = "changed"
            if picking == self.picking:
                raise ValueError("carrier error")
            picking.delivery_state = "in_transit"

        with patch.object(
            type(self.carrier), "fixed_tracking_state_update", update, create=True
        ):
            with self.assertRaisesRegex(ValueError, "carrier error"):
                self.picking.tracking_state_update()
            self.assertFalse(self.picking.tracking_state)
            (self.picking | other).with_context(cron_id=1).tracking_state_update()
        self.assertFalse(self.picking.tracking_state)
        self.assertEqual(self.picking.pod_error, "carrier error")
        self.assertEqual(other.delivery_state, "in_transit")

    def test_copy_does_not_copy_tracking(self):
        self.picking.write(
            {
                "date_shipped": fields.Date.today(),
                "date_delivered": fields.Datetime.now(),
                "tracking_json": {"status": "delivered"},
                "tracking_state": "delivered",
                "tracking_state_history": "history",
                "delivery_state": "customer_delivered",
                "pod_file": BinaryBytes(b"test"),
                "pod_filename": "pod.pdf",
                "pod_error": "error",
            }
        )
        copy = self.picking.copy()
        for name in (
            "date_shipped",
            "date_delivered",
            "tracking_json",
            "tracking_state",
            "tracking_state_history",
            "delivery_state",
            "pod_file",
            "pod_filename",
            "pod_error",
        ):
            self.assertFalse(copy[name], name)
