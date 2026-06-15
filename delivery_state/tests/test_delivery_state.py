# Copyright 2020 Trey, Kilobytes de Soluciones
# Copyright 2020 FactorLibre
# Copyright 2026 Raumschmiede GmbH
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import mock
from freezegun import freeze_time
from odoo_test_helper import FakeModelLoader

from odoo import fields
from odoo.tests import Form
from odoo.tests.common import SavepointCase
from odoo.tools import float_compare

from ..models.stock_picking import (
    DELIVERY_STATE_CANCELED,
    DELIVERY_STATE_CUS_DELIVERED,
    DELIVERY_STATE_INCIDENCE,
    DELIVERY_STATE_NO_UPDATE,
    DELIVERY_STATE_SHIPPING_RECORDED,
)


class TestDeliveryState(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.loader = FakeModelLoader(cls.env, cls.__module__)
        cls.loader.backup_registry()
        from .delivery_carrier import DeliveryCarrier

        cls.loader.update_registry((DeliveryCarrier,))

        product_shipping_cost = cls.env["product.product"].create(
            {
                "type": "service",
                "name": "Shipping costs",
                "standard_price": 10,
                "list_price": 100,
            }
        )
        cls.carrier_fixed = cls.env["delivery.carrier"].create(
            {
                "name": "Fixed carrier",
                "delivery_type": "fixed",
                "product_id": product_shipping_cost.id,
                "fixed_price": 99.99,
            }
        )
        cls.carrier_test = cls.env["delivery.carrier"].create(
            {
                "name": "Test carrier",
                "delivery_type": "test",
                "product_id": product_shipping_cost.id,
            }
        )
        cls.product = cls.env["product.product"].create(
            {"name": "Test product", "type": "product"}
        )
        cls._set_stock(cls.product, 100)

        cls.partner = cls.env["res.partner"].create({"name": "Mr. Odoo"})
        cls.partner_shipping = cls.env["res.partner"].create(
            {"name": "Mr. Odoo (shipping)"}
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

    @classmethod
    def tearDownClass(cls):
        cls.loader.restore_registry()
        super().tearDownClass()

    @classmethod
    def _set_stock(cls, product, qty):
        return cls.env["stock.quant"]._update_available_quantity(
            product,
            cls.env.ref("stock.stock_location_stock"),
            qty,
        )

    def test_delivery_state(self):
        delivery_wizard = Form(
            self.env["choose.delivery.carrier"].with_context(
                {
                    "default_order_id": self.sale.id,
                    "default_carrier_id": self.carrier_fixed,
                }
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
        self.assertEqual(picking.carrier_id, self.carrier_fixed)
        picking.action_confirm()
        picking.action_assign()
        picking.send_to_shipper()
        self.assertEqual(picking.delivery_state, DELIVERY_STATE_SHIPPING_RECORDED)
        self.assertTrue(picking.date_shipped)
        self.assertFalse(picking.tracking_state_history)
        picking.tracking_state_update()
        self.assertEqual(picking.delivery_state, DELIVERY_STATE_NO_UPDATE)
        picking.date_delivered = fields.Datetime.now()
        with self.assertRaises(NotImplementedError):
            picking.cancel_shipment()
        self.env["delivery.carrier"]._patch_method(
            "fixed_cancel_shipment", lambda *args: True
        )
        picking.cancel_shipment()
        self.assertEqual(picking.delivery_state, DELIVERY_STATE_CANCELED)
        self.assertFalse(picking.date_shipped)
        self.assertFalse(picking.date_delivered)

    def test_delivery_state_no_tracking(self):
        self.carrier_test.write({"track_carrier_state": False})
        delivery_wizard = Form(
            self.env["choose.delivery.carrier"].with_context(
                {
                    "default_order_id": self.sale.id,
                    "default_carrier_id": self.carrier_test,
                }
            )
        )
        choose_delivery_carrier = delivery_wizard.save()
        choose_delivery_carrier.button_confirm()
        self.sale.action_confirm()
        picking = self.sale.picking_ids[0]
        picking.action_confirm()
        picking.action_assign()
        picking.send_to_shipper()
        self.assertEqual(picking.delivery_state, DELIVERY_STATE_NO_UPDATE)

    def test_delivery_confirmation_send(self):
        """Check that the shipping notification is sent to the right partner"""
        self.env.ref("delivery_state.delivery_notification").auto_delete = False
        self.sale.action_confirm()
        previous_mails = self.env["mail.mail"].search(
            [("partner_ids", "in", self.partner.ids)]
        )
        self.assertFalse(previous_mails)
        picking = self.sale.picking_ids
        picking.carrier_id = self.carrier_test
        picking.company_id.stock_move_email_validation = True
        delivery_template = self.env.ref("delivery_state.delivery_notification")
        picking.company_id.stock_mail_confirmation_template_id = delivery_template
        picking.move_lines.quantity_done = 1
        picking._action_done()
        mail = self.env["mail.message"].search(
            [("partner_ids", "in", self.partner.ids)]
        )
        self.assertTrue("TESTTRACK" in mail.body)

    def test_days_fetch_tracking_state_update(self):
        self.sale.action_confirm()
        picking = self.sale.picking_ids
        picking.carrier_id = self.carrier_test
        picking.move_lines.quantity_done = 1
        with freeze_time("2026-03-01"):
            picking._action_done()
        picking.tracking_state_update()
        # No days are set on the carrier, so delivery_state must be the same as before
        self.assertEqual(picking.delivery_state, DELIVERY_STATE_SHIPPING_RECORDED)

        self.carrier_test.days_fetch_tracking_state_update = 5
        # date_shipped is not within the time range, delivery_state must be set
        picking.tracking_state_update()
        self.assertEqual(picking.delivery_state, DELIVERY_STATE_NO_UPDATE)

        data = {"delivery_state": DELIVERY_STATE_INCIDENCE}
        with freeze_time("2026-03-30"):
            picking.with_context(track_data=data).tracking_state_update()
        # Doesn't matter whether the API returned a new delivery state as long as it is
        # not a final state. State must be set to no_update
        self.assertEqual(picking.delivery_state, DELIVERY_STATE_NO_UPDATE)

        data = {"delivery_state": DELIVERY_STATE_CUS_DELIVERED}
        with freeze_time("2026-03-30"):
            picking.with_context(track_data=data).tracking_state_update()

        # API returned a final state, delivery_state must not be overwritten
        self.assertEqual(picking.delivery_state, DELIVERY_STATE_CUS_DELIVERED)

    def test_cron_pickings(self):
        self.env.ref("stock.warehouse0").delivery_steps = "pick_pack_ship"
        self.sale.action_confirm()

        # Set PICK to done
        pick = self.sale.picking_ids.filtered(lambda p: p.state == "assigned")
        for ml in pick.move_line_ids:
            ml.qty_done = ml.product_uom_qty
        pick.button_validate()
        pick.carrier_id = self.carrier_test

        # Set PACK to done. Call carrier API with this picking
        pack = self.sale.picking_ids.filtered(lambda p: p.state == "assigned")
        for ml in pack.move_line_ids:
            ml.qty_done = ml.product_uom_qty
        pack.carrier_id = self.carrier_test
        pack.button_validate()
        self.assertTrue(pack)

        # SET OUT to done
        ship = self.sale.picking_ids.filtered(lambda p: p.state == "assigned")
        for ml in ship.move_line_ids:
            ml.qty_done = ml.product_uom_qty
        ship.button_validate()
        # NOTE: On version >= 18.0 use the carrier on the picking and the PACK rule
        # should propagate the carrier to the OUT
        ship.carrier_id = self.carrier_test

        with mock.patch.object(
            type(self.env["stock.picking"]),
            "tracking_state_update",
            autospec=True,
        ) as mocked:
            self.env.ref(
                "delivery_state.ir_cron_delivery_state"
            ).method_direct_trigger()

            # As only the PACK picking was sent to the carrier API only for this
            # the tracking state must be updated even if the other pickings have
            # a carrier set
            mocked.assert_called_once_with(pack)
