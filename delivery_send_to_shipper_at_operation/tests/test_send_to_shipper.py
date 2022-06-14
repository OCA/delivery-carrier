# Copyright 2021 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from unittest import mock

from lxml import etree

from odoo.tests.common import SavepointCase
from odoo.tools.safe_eval import safe_eval

SEND_SHIPPING_RETURN_VALUE = [{"exact_price": 10.0, "tracking_number": "TEST"}]


class TestDeliverySendToShipper(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.wh = cls.env.ref("stock.warehouse0")
        cls.wh.delivery_steps = "pick_pack_ship"
        cls.stock_location = cls.env.ref("stock.stock_location_stock")
        # cls.pack_location = cls.wh.wh_pack_stock_loc_id
        cls.ship_location = cls.wh.wh_output_stock_loc_id
        cls.customer_location = cls.env.ref("stock.stock_location_customers")
        # put product in stock
        cls.product = cls.env.ref("product.product_delivery_01")
        cls.env["stock.quant"]._update_available_quantity(
            cls.product,
            cls.stock_location,
            10.0,
        )
        # create carriers
        cls.delivery_fee = cls.env.ref("delivery.product_product_delivery")
        cls.carrier_on_ship = cls.env["delivery.carrier"].create(
            {
                "name": "Carrier On Ship",
                "product_id": cls.delivery_fee.id,
                "integration_level": "rate_and_ship",
                "send_delivery_notice_on": "ship",
                "invoice_policy": "real",
            }
        )
        cls.carrier_on_pack = cls.env["delivery.carrier"].create(
            {
                "name": "Carrier On Pack",
                "product_id": cls.delivery_fee.id,
                "integration_level": "rate_and_ship",
                "send_delivery_notice_on": "custom",
                "send_delivery_notice_picking_type_ids": [
                    (6, 0, cls.wh.pack_type_id.ids)
                ],
                "invoice_policy": "real",
            }
        )
        # create a pick/pack/ship transfer
        cls.ship_move = cls.env["stock.move"].create(
            {
                "name": cls.product.display_name,
                "product_id": cls.product.id,
                "product_uom_qty": 10.0,
                "product_uom": cls.product.uom_id.id,
                "location_id": cls.ship_location.id,
                "location_dest_id": cls.customer_location.id,
                "warehouse_id": cls.wh.id,
                "picking_type_id": cls.wh.out_type_id.id,
                "procure_method": "make_to_order",
                "state": "draft",
            }
        )
        cls.ship_move._assign_picking()
        cls.ship_move._action_confirm()
        cls.pack_move = cls.ship_move.move_orig_ids[0]
        cls.pick_move = cls.pack_move.move_orig_ids[0]
        cls.picking = cls.pick_move.picking_id
        cls.packing = cls.pack_move.picking_id
        cls.shipping = cls.ship_move.picking_id
        cls.picking.action_assign()
        # Assign an empty order to transfers in a ugly way to ease test
        # (no SO line = no fee added by the delivery module)
        cls.order = cls.env["sale.order"].create(
            {"partner_id": cls.env.ref("base.res_partner_1").id}
        )
        (cls.picking | cls.packing | cls.shipping).sale_id = cls.order

    def _validate_picking(self, picking):
        for ml in picking.move_line_ids:
            ml.qty_done = ml.product_uom_qty
        picking._action_done()

    def test_send_to_shipper_on_ship(self):
        """Check sending of delivery notification on ship.

        No delivery notification is sent to the carrier when the pack is
        validated (std Odoo behavior).
        """
        with mock.patch.object(
            type(self.carrier_on_ship),
            "send_shipping",
            return_value=SEND_SHIPPING_RETURN_VALUE,
        ):
            self.shipping.carrier_id = self.carrier_on_ship
            # Validate the pick: nothing happen, as usual
            self._validate_picking(self.picking)
            self.assertEqual(self.picking.state, "done")
            # Validate the pack: delivery notification is not sent
            self.assertFalse(self.order.order_line)  # No fee
            self._validate_picking(self.packing)
            self.assertEqual(self.packing.state, "done")
            self.assertFalse(self.shipping.delivery_notification_sent)
            self.assertFalse(self.order.order_line)  # Still no fee added
            # Validate the ship: delivery notification is sent
            self._validate_picking(self.shipping)
            self.assertEqual(self.shipping.state, "done")
            self.assertFalse(self.shipping.delivery_notification_sent)
            self.assertIn(self.delivery_fee, self.order.order_line.product_id)

    def test_send_to_shipper_on_pack(self):
        """Check sending of delivery notification on pack.

        The delivery notification is sent to the carrier when the pack is
        validated (the carrier has been configured this way), so the delivery
        notification should not be sent again when the ship is validated.
        Furthermore, the delivery cost should still be added to the SO when
        the ship is validated (not the pack).
        """
        with mock.patch.object(
            type(self.carrier_on_pack),
            "send_shipping",
            return_value=SEND_SHIPPING_RETURN_VALUE,
        ):
            self.shipping.carrier_id = self.carrier_on_pack
            self._validate_picking(self.picking)
            self.assertEqual(self.picking.state, "done")
            # Validate the pack: delivery notification is sent with the
            # carrier of the ship, and this one is flagged accordingly
            self.assertFalse(self.order.order_line)  # No fee
            self._validate_picking(self.packing)
            self.assertEqual(self.packing.state, "done")
            self.assertTrue(self.shipping.delivery_notification_sent)
            self.assertFalse(self.order.order_line)  # Still no fee added
            self.assertEqual(self.packing.carrier_price, self.shipping.carrier_price)
            self.assertEqual(
                self.packing.carrier_tracking_ref, self.shipping.carrier_tracking_ref
            )
            # Validate the ship: no delivery notification is sent to the carrier
            # as it has already been done during the validation of the pack,
            # but delivery fee has been added to the SO
            self._validate_picking(self.shipping)
            self.assertEqual(self.shipping.state, "done")
            self.assertTrue(self.shipping.delivery_notification_sent)
            self.assertIn(self.delivery_fee, self.order.order_line.product_id)

    def test_send_to_shipper_on_pack_multi_tracking(self):
        """Check sending of delivery notification on pack with multi tracking."""

        with mock.patch.object(
            type(self.carrier_on_pack),
            "send_shipping",
            return_value=SEND_SHIPPING_RETURN_VALUE,
        ):
            carrier_tracking_ref = "99999"
            self.shipping.carrier_id = self.carrier_on_pack
            self.shipping.carrier_tracking_ref = carrier_tracking_ref

            self._validate_picking(self.picking)
            self.assertEqual(self.picking.state, "done")

            self.assertFalse(self.order.order_line)
            self._validate_picking(self.packing)

            self.assertEqual(self.packing.state, "done")
            self.assertTrue(self.shipping.delivery_notification_sent)
            self.assertFalse(self.order.order_line)
            self.assertEqual(self.packing.carrier_price, self.shipping.carrier_price)

            # Check multi tracking
            self.assertEqual(
                self.shipping.carrier_tracking_ref,
                carrier_tracking_ref + "," + self.packing.carrier_tracking_ref,
            )

            self._validate_picking(self.shipping)
            self.assertEqual(self.shipping.state, "done")
            self.assertTrue(self.shipping.delivery_notification_sent)
            self.assertIn(self.delivery_fee, self.order.order_line.product_id)

    def test_picking_fields_view_get(self):
        """Check that the invisible domain of "Send to Shipper" button
        takes into account the 'delivery_notification_sent' flag.
        """
        view = self.shipping.fields_view_get()
        doc = etree.XML(view["arch"])
        xpath_expr = "//button[@name='send_to_shipper']"
        button_send_to_shipper = doc.xpath(xpath_expr)[0]
        attrs_str = button_send_to_shipper.attrib["attrs"]
        attrs = safe_eval(attrs_str)
        self.assertIn(("delivery_notification_sent", "=", True), attrs["invisible"])
