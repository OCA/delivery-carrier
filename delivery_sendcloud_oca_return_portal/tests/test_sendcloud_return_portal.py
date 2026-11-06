# Copyright 2026 arielbarreiros96 (https://github.com/arielbarreiros96)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl)

import json
from datetime import timedelta

from odoo import Command, fields
from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged
from odoo.tools import mute_logger


@tagged("post_install", "-at_install")
class TestSendcloudReturnPortal(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create({"name": "Return Customer"})
        cls.product_a = cls.env["product.product"].create(
            {"name": "Tracked Product", "default_code": "SKU-A", "is_storable": True}
        )
        cls.product_b = cls.env["product.product"].create(
            {"name": "Other Product", "default_code": "SKU-B", "is_storable": True}
        )
        cls.picking = cls._create_done_delivery(
            [(cls.product_a, 3.0), (cls.product_b, 2.0)]
        )
        cls.env["sendcloud.integration"].create(
            {
                "shop_name": "Test Shop",
                "public_key": "test-public-key",
                "secret_key": "test-secret-key",
                "company_id": cls.env.company.id,
            }
        )
        cls.return_carrier = cls.env["delivery.carrier"].create(
            {
                "name": "Sendcloud Easy Retour",
                "delivery_type": "sendcloud",
                "sendcloud_code": 1520,
                "company_id": cls.env.company.id,
                "product_id": cls.env["product.product"]
                .create({"name": "Return Shipping", "type": "service"})
                .id,
            }
        )
        cls.env["sendcloud.parcel.status"].create(
            [
                {"sendcloud_code": "1000", "message": "Ready to send"},
                {"sendcloud_code": "3", "message": "En route to sorting center"},
                {"sendcloud_code": "2000", "message": "Cancelled"},
            ]
        )
        cls.outgoing_parcel = cls.env["sendcloud.parcel"].create(
            {
                "name": "Outgoing Parcel",
                "sendcloud_code": 111,
                "picking_id": cls.picking.id,
                "company_id": cls.env.company.id,
            }
        )

    @classmethod
    def _create_done_delivery(cls, lines):
        picking_type = cls.env.ref("stock.picking_type_out")
        picking = cls.env["stock.picking"].create(
            {
                "partner_id": cls.partner.id,
                "picking_type_id": picking_type.id,
                "location_id": picking_type.default_location_src_id.id,
                "location_dest_id": cls.env.ref("stock.stock_location_customers").id,
                "move_ids": [
                    Command.create(
                        {
                            "product_id": product.id,
                            "product_uom_qty": qty,
                            "product_uom": product.uom_id.id,
                        }
                    )
                    for product, qty in lines
                ],
            }
        )
        picking.action_confirm()
        for move in picking.move_ids:
            move.quantity = move.product_uom_qty
            move.picked = True
        picking.button_validate()
        return picking

    def _create_return(
        self,
        items,
        created_at="2026-09-10T10:00:00+02:00",
        tracking="TRACK-RETURN-1",
        label_cost=0.0,
    ):
        incoming_parcel = self.env["sendcloud.parcel"].create(
            {
                "name": "Incoming Parcel",
                "sendcloud_code": 222,
                "company_id": self.env.company.id,
                "is_return": True,
                "tracking_number": tracking,
                "shipment": "{'id': 1520, 'name': 'bpack Easy Retour 0-10kg'}",
                "parcel_item_ids": [Command.create(values) for values in items],
            }
        )
        return self.env["sendcloud.return"].create(
            {
                "sendcloud_code": 999,
                "company_id": self.env.company.id,
                "outgoing_parcel_code": self.outgoing_parcel.sendcloud_code,
                "incoming_parcel_code": incoming_parcel.sendcloud_code,
                "created_at": created_at,
                "status_display": "Announced",
                "delivery_option": "drop_off_point",
                "message": "Too big",
                "label_cost": label_cost,
            }
        )

    def test_return_creates_picking_matched_by_sku(self):
        sendcloud_return = self._create_return(
            [{"description": "Tracked Product", "sku": "SKU-A", "quantity": 2}]
        )
        sendcloud_return.action_create_odoo_return()
        picking = sendcloud_return.picking_id
        self.assertTrue(picking, msg="A return operation should have been created")
        self.assertEqual(
            sendcloud_return.original_picking_id,
            self.picking,
            msg="The return should point back to the original delivery",
        )
        self.assertEqual(picking.picking_type_id.code, "incoming")
        self.assertEqual(len(picking.move_ids), 1)
        self.assertEqual(picking.move_ids.product_id, self.product_a)
        self.assertEqual(picking.move_ids.product_uom_qty, 2.0)

    def test_unknown_sku_falls_back_to_generic_product(self):
        sendcloud_return = self._create_return(
            [{"description": "Mystery Item", "sku": "SKU-NOPE", "quantity": 1}]
        )
        sendcloud_return.action_create_odoo_return()
        move = sendcloud_return.picking_id.move_ids
        self.assertEqual(
            move.product_id,
            self.env.ref(
                "delivery_sendcloud_oca_return_portal."
                "product_sendcloud_unidentified_return"
            ),
            msg="An unmatched SKU should fall back to the generic product",
        )
        self.assertEqual(
            move.description_picking,
            "Mystery Item",
            msg="The warehouse needs the Sendcloud description to identify the goods",
        )

    def test_partial_sync_does_not_archive_other_returns(self):
        other = self._create_return(
            [{"description": "x", "sku": "SKU-A", "quantity": 1}]
        )
        self.env["sendcloud.return"].sendcloud_create_or_update_returns(
            {"id": 12345, "status": "delivered"}, self.env.company
        )
        self.assertTrue(
            other.active,
            msg="Upserting one return must not archive the others",
        )

    def test_return_details_posted_on_picking(self):
        sendcloud_return = self._create_return(
            [{"description": "Tracked Product", "sku": "SKU-A", "quantity": 1}]
        )
        sendcloud_return.action_create_odoo_return()
        bodies = "".join(sendcloud_return.picking_id.message_ids.mapped("body"))
        self.assertIn(
            "Too big", bodies, msg="The customer message should reach the warehouse"
        )

    def test_returns_before_start_date_are_ignored(self):
        self.env.company.sendcloud_return_picking_start_date = "2026-09-01"
        old = self._create_return(
            [{"description": "Tracked Product", "sku": "SKU-A", "quantity": 1}],
            created_at="2026-08-31T10:00:00+02:00",
        )
        old._create_odoo_returns()
        self.assertFalse(
            old.picking_id,
            msg="A return predating the start date must not create an operation",
        )

    def test_returns_after_start_date_are_created(self):
        self.env.company.sendcloud_return_picking_start_date = "2026-09-01"
        recent = self._create_return(
            [{"description": "Tracked Product", "sku": "SKU-A", "quantity": 1}],
            created_at="2026-09-02T10:00:00+02:00",
        )
        recent._create_odoo_returns()
        self.assertTrue(
            recent.picking_id,
            msg="A return created after the start date must be processed",
        )

    def test_old_return_still_processed_by_hand(self):
        self.env.company.sendcloud_return_picking_start_date = "2026-09-01"
        old = self._create_return(
            [{"description": "Tracked Product", "sku": "SKU-A", "quantity": 1}],
            created_at="2026-08-31T10:00:00+02:00",
        )
        old.action_create_odoo_return()
        self.assertTrue(
            old.picking_id,
            msg="The manual button must ignore the start date",
        )

    @mute_logger(
        "odoo.addons.delivery_sendcloud_oca_return_portal.models.sendcloud_return"
    )
    def test_failed_creation_leaves_no_empty_operation(self):
        sendcloud_return = self._create_return(
            [{"description": "Tracked Product", "sku": "SKU-A", "quantity": 1}]
        )
        before = self.env["stock.picking"].search_count(
            [("return_id", "=", self.picking.id)]
        )

        def explode(*args, **kwargs):
            raise ValueError("Sendcloud went sideways")

        self.patch(type(sendcloud_return), "_post_return_details", explode)
        sendcloud_return._create_odoo_returns()
        self.assertEqual(
            self.env["stock.picking"].search_count(
                [("return_id", "=", self.picking.id)]
            ),
            before,
            msg="A failed attempt must not leave an empty return operation behind",
        )
        self.assertFalse(sendcloud_return.picking_id)
        self.assertIn("sideways", sendcloud_return.odoo_return_error)

    def test_item_return_message_reaches_the_warehouse(self):
        sendcloud_return = self._create_return(
            [
                {
                    "description": "Tracked Product",
                    "sku": "SKU-A",
                    "quantity": 1,
                    "return_message": "I don't like it <b>anymore</b>",
                }
            ]
        )
        sendcloud_return.action_create_odoo_return()
        bodies = "".join(sendcloud_return.picking_id.message_ids.mapped("body"))
        self.assertIn("I don't like it", bodies)
        self.assertNotIn(
            "&lt;br", bodies, msg="Line breaks must render, not show as markup"
        )
        self.assertIn(
            "&lt;b&gt;",
            bodies,
            msg="Text coming from Sendcloud must be escaped, not rendered",
        )

    def test_return_operation_carries_the_return_carrier_and_tracking(self):
        sendcloud_return = self._create_return(
            [{"description": "Tracked Product", "sku": "SKU-A", "quantity": 1}]
        )
        sendcloud_return._create_odoo_returns()
        picking = sendcloud_return.picking_id
        self.assertEqual(
            picking.carrier_id,
            self.return_carrier,
            msg="The operation must use the return shipping method",
        )
        self.assertNotEqual(
            picking.carrier_id,
            self.picking.carrier_id,
            msg="The outgoing shipping method must not leak onto the return",
        )
        self.assertEqual(picking.carrier_tracking_ref, "TRACK-RETURN-1")

    def test_incoming_parcel_is_linked_to_the_return_operation(self):
        sendcloud_return = self._create_return(
            [{"description": "Tracked Product", "sku": "SKU-A", "quantity": 1}]
        )
        sendcloud_return._create_odoo_returns()
        picking = sendcloud_return.picking_id
        self.assertEqual(
            picking.sendcloud_parcel_ids,
            sendcloud_return.incoming_parcel_id,
            msg="The return parcel must be reachable from the operation",
        )

    def test_shipment_link_is_repaired_on_an_existing_operation(self):
        sendcloud_return = self._create_return(
            [{"description": "Tracked Product", "sku": "SKU-A", "quantity": 1}]
        )
        sendcloud_return.action_create_odoo_return()
        picking = sendcloud_return.picking_id
        picking.with_context(skip_sync_picking_to_sendcloud=True).write(
            {"carrier_id": False, "carrier_tracking_ref": False}
        )
        sendcloud_return.incoming_parcel_id.picking_id = False
        sendcloud_return.action_create_odoo_return()
        self.assertEqual(sendcloud_return.picking_id, picking)
        self.assertEqual(picking.carrier_id, self.return_carrier)
        self.assertEqual(picking.carrier_tracking_ref, "TRACK-RETURN-1")
        self.assertEqual(
            picking.sendcloud_parcel_ids, sendcloud_return.incoming_parcel_id
        )

    def test_a_second_sync_does_not_duplicate_the_return_operation(self):
        sendcloud_return = self._create_return(
            [{"description": "Tracked Product", "sku": "SKU-A", "quantity": 1}]
        )
        sendcloud_return._create_odoo_returns()
        picking = sendcloud_return.picking_id
        self.assertTrue(picking)
        before = self.env["stock.picking"].search_count(
            [("return_id", "=", self.picking.id)]
        )
        sendcloud_return._create_odoo_returns()
        self.assertEqual(
            sendcloud_return.picking_id,
            picking,
            msg="A second sync must not re-point the return at a new operation",
        )
        self.assertEqual(
            self.env["stock.picking"].search_count(
                [("return_id", "=", self.picking.id)]
            ),
            before,
            msg="A second sync must not create a duplicate return operation",
        )

    def test_full_sync_payload_twice_creates_one_operation(self):
        sendcloud_return = self._create_return(
            [{"description": "Tracked Product", "sku": "SKU-A", "quantity": 1}]
        )
        payload = {
            "id": sendcloud_return.sendcloud_code,
            "incoming_parcel": sendcloud_return.incoming_parcel_code,
            "outgoing_parcel": sendcloud_return.outgoing_parcel_code,
            "created_at": "2026-09-10T10:00:00+02:00",
            "status": "open",
        }
        model = self.env["sendcloud.return"]
        model.sendcloud_create_or_update_returns(payload, self.env.company)
        first = sendcloud_return.picking_id
        model.sendcloud_create_or_update_returns(payload, self.env.company)
        self.assertEqual(
            sendcloud_return.picking_id,
            first,
            msg="Re-syncing the same return must not create a second operation",
        )
        self.assertEqual(
            self.env["stock.picking"].search_count(
                [("return_id", "=", self.picking.id)]
            ),
            1,
            msg="Re-syncing the same return must not create a second operation",
        )

    def test_creating_the_operation_does_not_clone_the_sendcloud_return(self):
        sendcloud_return = self._create_return(
            [{"description": "Tracked Product", "sku": "SKU-A", "quantity": 1}]
        )
        code = sendcloud_return.sendcloud_code
        sendcloud_return._create_odoo_returns()
        self.assertEqual(
            self.env["sendcloud.return"]
            .with_context(active_test=False)
            .search_count([("sendcloud_code", "=", code)]),
            1,
            msg="Copying the original delivery must not clone its Sendcloud returns",
        )
        self.assertTrue(sendcloud_return.active)

    def test_operation_is_adopted_when_this_module_loses_its_link(self):
        sendcloud_return = self._create_return(
            [{"description": "Tracked Product", "sku": "SKU-A", "quantity": 1}]
        )
        sendcloud_return._create_odoo_returns()
        picking = sendcloud_return.picking_id
        before = self.env["stock.picking"].search_count(
            [("return_id", "=", self.picking.id)]
        )
        sendcloud_return.write({"picking_id": False, "original_picking_id": False})
        sendcloud_return._create_odoo_returns()
        self.assertEqual(
            sendcloud_return.picking_id,
            picking,
            msg="A lost link must be recovered from the parcel, not rebuilt",
        )
        self.assertEqual(
            self.env["stock.picking"].search_count(
                [("return_id", "=", self.picking.id)]
            ),
            before,
            msg="A lost link must not produce a duplicate return operation",
        )
        self.assertEqual(sendcloud_return.original_picking_id, self.picking)

    def test_tracking_assigned_after_the_operation_still_reaches_it(self):
        sendcloud_return = self._create_return(
            [{"description": "Tracked Product", "sku": "SKU-A", "quantity": 1}],
            tracking=False,
        )
        sendcloud_return._create_odoo_returns()
        picking = sendcloud_return.picking_id
        self.assertFalse(
            picking.carrier_tracking_ref,
            msg="Sendcloud had not issued a label yet",
        )
        self.assertEqual(
            picking.carrier_id,
            self.return_carrier,
            msg="The shipping method is known before the label is",
        )
        sendcloud_return.incoming_parcel_id.tracking_number = "LATE-TRACK-9"
        self.assertEqual(
            picking.carrier_tracking_ref,
            "LATE-TRACK-9",
            msg="A tracking number issued later must still reach the operation",
        )

    def test_late_tracking_does_not_overwrite_an_existing_reference(self):
        sendcloud_return = self._create_return(
            [{"description": "Tracked Product", "sku": "SKU-A", "quantity": 1}]
        )
        sendcloud_return._create_odoo_returns()
        picking = sendcloud_return.picking_id
        self.assertEqual(picking.carrier_tracking_ref, "TRACK-RETURN-1")
        sendcloud_return.incoming_parcel_id.tracking_number = "SOMETHING-ELSE"
        self.assertEqual(
            picking.carrier_tracking_ref,
            "TRACK-RETURN-1",
            msg="An established tracking reference must not be silently replaced",
        )

    def _patch_cancel_parcel(self, response):
        integration = self.env.company.sendcloud_default_integration_id
        calls = []

        def cancel_parcel(self, code):
            calls.append(code)
            return response

        self.patch(type(integration), "cancel_parcel", cancel_parcel)
        return calls

    def test_cancelling_the_operation_cancels_the_parcel_at_sendcloud(self):
        sendcloud_return = self._create_return(
            [{"description": "Tracked Product", "sku": "SKU-A", "quantity": 1}]
        )
        sendcloud_return._create_odoo_returns()
        picking = sendcloud_return.picking_id
        calls = self._patch_cancel_parcel(
            {"status": "cancelled", "message": "Parcel has been cancelled"}
        )
        picking.action_cancel()
        self.assertEqual(
            calls,
            [sendcloud_return.incoming_parcel_id.sendcloud_code],
            msg="Cancelling in Odoo must cancel the parcel at Sendcloud",
        )
        self.assertEqual(picking.state, "cancel")
        self.assertEqual(sendcloud_return.incoming_parcel_id.sendcloud_status, "2000")

    def test_a_refusal_from_sendcloud_blocks_the_odoo_cancellation(self):
        sendcloud_return = self._create_return(
            [{"description": "Tracked Product", "sku": "SKU-A", "quantity": 1}]
        )
        sendcloud_return._create_odoo_returns()
        picking = sendcloud_return.picking_id
        self._patch_cancel_parcel(
            {"error": {"code": 410, "message": "Parcel is already in transit"}}
        )
        with self.assertRaises(UserError) as caught:
            picking.action_cancel()
        self.assertIn("already in transit", str(caught.exception))
        self.assertNotEqual(
            picking.state,
            "cancel",
            msg="Odoo must not cancel what Sendcloud refused to cancel",
        )

    def test_sendcloud_cancelling_the_parcel_cancels_the_reception(self):
        sendcloud_return = self._create_return(
            [{"description": "Tracked Product", "sku": "SKU-A", "quantity": 1}]
        )
        sendcloud_return._create_odoo_returns()
        picking = sendcloud_return.picking_id
        self.assertEqual(picking.state, "assigned")
        sendcloud_return.incoming_parcel_id.sendcloud_status = "2000"
        self.assertEqual(
            picking.state,
            "cancel",
            msg="A return cancelled at Sendcloud must not leave the warehouse waiting",
        )

    def _create_open_delivery(self):
        picking_type = self.env.ref("stock.picking_type_out")
        delivery = self.env["stock.picking"].create(
            {
                "partner_id": self.partner.id,
                "carrier_id": self.return_carrier.id,
                "picking_type_id": picking_type.id,
                "location_id": picking_type.default_location_src_id.id,
                "location_dest_id": self.env.ref("stock.stock_location_customers").id,
                "move_ids": [
                    Command.create(
                        {
                            "product_id": self.product_a.id,
                            "product_uom_qty": 1.0,
                            "product_uom": self.product_a.uom_id.id,
                        }
                    )
                ],
            }
        )
        delivery.action_confirm()
        return delivery

    def test_sendcloud_cancelling_a_delivery_cancels_it_in_odoo_too(self):
        delivery = self._create_open_delivery()
        parcel = self.env["sendcloud.parcel"].create(
            {
                "name": "Open Delivery Parcel",
                "sendcloud_code": 333,
                "company_id": self.env.company.id,
                "picking_id": delivery.id,
            }
        )
        parcel.sendcloud_status = "2000"
        self.assertEqual(
            delivery.state,
            "cancel",
            msg="A delivery cancelled at Sendcloud must be cancelled in Odoo",
        )

    def test_reacting_to_sendcloud_does_not_push_the_cancellation_back(self):
        delivery = self._create_open_delivery()
        parcel = self.env["sendcloud.parcel"].create(
            {
                "name": "Open Delivery Parcel",
                "sendcloud_code": 334,
                "company_id": self.env.company.id,
                "picking_id": delivery.id,
            }
        )
        calls = self._patch_cancel_parcel({"status": "cancelled"})
        deletions = []
        integration = self.env.company.sendcloud_default_integration_id

        def delete_shipments(self, integration_id, post_data):
            deletions.append(post_data)
            return {}

        self.patch(type(integration), "delete_shipments", delete_shipments)
        parcel.sendcloud_status = "2000"
        self.assertEqual(delivery.state, "cancel")
        self.assertEqual(
            calls,
            [],
            msg="Sendcloud told us it cancelled, we must not tell it back",
        )
        self.assertEqual(
            deletions,
            [],
            msg="Sendcloud told us it cancelled, we must not delete the order there",
        )

    def test_a_done_transfer_cancelled_at_sendcloud_raises_an_activity(self):
        self.outgoing_parcel.picking_id = self.picking
        self.picking.activity_ids.unlink()
        self.outgoing_parcel.sendcloud_status = "2000"
        self.assertEqual(
            self.picking.state,
            "done",
            msg="A done transfer cannot be cancelled",
        )
        self.assertTrue(
            self.picking.activity_ids,
            msg="A divergence Odoo cannot mirror must reach a human",
        )

    def test_a_return_cancelled_at_sendcloud_creates_no_operation(self):
        sendcloud_return = self._create_return(
            [{"description": "Tracked Product", "sku": "SKU-A", "quantity": 1}]
        )
        sendcloud_return.incoming_parcel_id.sendcloud_status = "2000"
        sendcloud_return._create_odoo_returns()
        self.assertFalse(
            sendcloud_return.picking_id,
            msg="A cancelled return must not produce a warehouse operation",
        )

    def test_return_label_cost_lands_on_the_operation(self):
        sendcloud_return = self._create_return(
            [{"description": "Tracked Product", "sku": "SKU-A", "quantity": 1}],
            label_cost=6.01,
        )
        sendcloud_return._create_odoo_returns()
        self.assertEqual(
            sendcloud_return.picking_id.carrier_price,
            6.01,
            msg="The return label cost must be visible on the operation",
        )

    def test_label_cost_priced_after_the_operation_still_reaches_it(self):
        sendcloud_return = self._create_return(
            [{"description": "Tracked Product", "sku": "SKU-A", "quantity": 1}]
        )
        sendcloud_return._create_odoo_returns()
        picking = sendcloud_return.picking_id
        self.assertEqual(
            picking.carrier_price,
            0.0,
            msg="Sendcloud had not priced the label yet",
        )
        sendcloud_return.label_cost = 6.01
        self.assertEqual(
            picking.carrier_price,
            6.01,
            msg="A label priced later must still reach the operation",
        )

    def _create_action(self, message):
        return self.env["sendcloud.action"].create(
            {
                "company_id": self.env.company.id,
                "message_type": "received",
                "action": message.get("action"),
                "message": json.dumps(message),
            }
        )

    def _patch_get_return(self, return_data):
        integration = self.env.company.sendcloud_default_integration_id
        calls = []

        def get_return(self, code):
            calls.append(code)
            return return_data

        self.patch(type(integration), "get_return", get_return)
        return calls

    def _patch_return_portal_url(self):
        integration = self.env.company.sendcloud_default_integration_id

        def get_return_portal_url(self, code):
            return {"url": None}

        self.patch(type(integration), "get_return_portal_url", get_return_portal_url)

    def test_a_return_webhook_creates_the_return_operation(self):
        sendcloud_return = self._create_return(
            [{"description": "Tracked Product", "sku": "SKU-A", "quantity": 1}]
        )
        self._patch_get_return(
            {
                "id": sendcloud_return.sendcloud_code,
                "incoming_parcel": sendcloud_return.incoming_parcel_code,
                "outgoing_parcel": sendcloud_return.outgoing_parcel_code,
                "created_at": "2026-09-10T10:00:00+02:00",
                "status": "open",
            }
        )
        action = self._create_action(
            {"action": "return_created", "return": {"id": 999}}
        )
        action.parse_result()
        self.assertTrue(
            sendcloud_return.picking_id,
            msg="A return announced by webhook must reach the warehouse",
        )
        self.assertEqual(action.record_id, sendcloud_return)

    def test_a_return_webhook_without_an_identifier_is_logged(self):
        action = self._create_action({"action": "return_created"})
        self.assertFalse(action.parse_result())
        self.assertTrue(action.error_message)

    def test_a_return_parcel_webhook_creates_the_return_operation(self):
        sendcloud_return = self._create_return(
            [{"description": "Tracked Product", "sku": "SKU-A", "quantity": 1}]
        )
        action = self._create_action(
            {
                "action": "parcel_status_changed",
                "parcel": {
                    "id": sendcloud_return.incoming_parcel_code,
                    "external_order_id": "",
                    "external_shipment_id": "",
                    "is_return": True,
                    "status": {"id": 1000, "message": "Ready to send"},
                },
            }
        )
        action.parse_result()
        self.assertTrue(
            sendcloud_return.picking_id,
            msg="A return parcel announced by webhook must reach the warehouse",
        )

    def test_an_outgoing_parcel_webhook_creates_no_return(self):
        self._patch_return_portal_url()
        action = self._create_action(
            {
                "action": "parcel_status_changed",
                "parcel": {
                    "id": self.outgoing_parcel.sendcloud_code,
                    "external_order_id": "",
                    "external_shipment_id": "",
                    "is_return": False,
                    "status": {"id": 1000, "message": "Ready to send"},
                },
            }
        )
        self.assertFalse(action._sendcloud_parse_return_parcel({"parcel": {}}))
        action.parse_result()
        self.assertFalse(
            self.env["sendcloud.return"].search([("picking_id", "=", self.picking.id)]),
            msg="A delivery parcel must not produce a return",
        )

    def test_an_unknown_return_parcel_triggers_a_full_sync(self):
        self._patch_return_portal_url()
        synced = []
        self.patch(
            type(self.env["sendcloud.return"]),
            "sendcloud_sync_returns",
            lambda self: synced.append(True),
        )
        action = self._create_action(
            {
                "action": "parcel_status_changed",
                "parcel": {
                    "id": 4242,
                    "external_order_id": "",
                    "external_shipment_id": "",
                    "is_return": True,
                    "status": {"id": 1000, "message": "Ready to send"},
                },
            }
        )
        action.parse_result()
        self.assertEqual(
            synced, [True], msg="An unknown return parcel must trigger a full sync"
        )

    def test_an_unreadable_webhook_is_left_to_the_base_module(self):
        action = self.env["sendcloud.action"].create(
            {
                "company_id": self.env.company.id,
                "message_type": "received",
                "action": "return_created",
                "message": "not json",
            }
        )
        self.assertFalse(action.parse_result())
        self.assertTrue(action.error_on_parsing)

    def _cancel_queued_return(self):
        sendcloud_return = self._create_return(
            [{"description": "Tracked Product", "sku": "SKU-A", "quantity": 1}]
        )
        sendcloud_return._create_odoo_returns()
        parcel = sendcloud_return.incoming_parcel_id
        parcel.sendcloud_status = "1000"
        self._patch_cancel_parcel(
            {"status": "queued", "message": "Parcel cancellation has been queued"}
        )
        sendcloud_return.picking_id.action_cancel()
        return parcel

    def _cancellation_warnings(self, parcel):
        return parcel.picking_id.activity_ids.filtered(
            lambda activity: "may still be active" in activity.note
        )

    def _age_parcel(self, parcel, days):
        self.env.flush_all()
        self.env.cr.execute(
            "UPDATE sendcloud_parcel SET write_date = %s WHERE id = %s",
            (fields.Datetime.now() - timedelta(days=days), parcel.id),
        )
        parcel.invalidate_recordset(["write_date"])

    def _patch_get_parcel(self, status):
        integration = self.env.company.sendcloud_default_integration_id
        calls = []

        def get_parcel(self, code):
            calls.append(code)
            return {"id": code, "status": {"id": status}}

        self.patch(type(integration), "get_parcel", get_parcel)
        return calls

    def test_a_queued_cancellation_is_a_cancellation(self):
        parcel = self._cancel_queued_return()
        self.assertEqual(parcel.picking_id.state, "cancel")
        self.assertEqual(parcel.sendcloud_status, "2000")

    def test_sendcloud_reporting_a_live_parcel_raises_nothing_at_once(self):
        parcel = self._cancel_queued_return()
        parcel.sendcloud_status = "3"
        self.assertFalse(
            self._cancellation_warnings(parcel),
            msg="Sendcloud has 14 days to cancel the label",
        )

    def test_the_scheduled_check_catches_a_failed_cancellation(self):
        parcel = self._cancel_queued_return()
        parcel.sendcloud_status = "3"
        self._age_parcel(parcel, 15)
        self._patch_get_parcel(3)
        self.env["sendcloud.parcel"].sendcloud_check_cancelled_parcels()
        self.assertTrue(self._cancellation_warnings(parcel))

    def test_the_scheduled_check_stays_silent_when_sendcloud_confirms(self):
        parcel = self._cancel_queued_return()
        parcel.sendcloud_status = "3"
        self._age_parcel(parcel, 15)
        self._patch_get_parcel(2000)
        self.env["sendcloud.parcel"].sendcloud_check_cancelled_parcels()
        self.assertEqual(parcel.sendcloud_status, "2000")
        self.assertFalse(self._cancellation_warnings(parcel))

    def test_the_scheduled_check_waits_for_sendcloud_to_finish(self):
        parcel = self._cancel_queued_return()
        parcel.sendcloud_status = "3"
        calls = self._patch_get_parcel(3)
        self.env["sendcloud.parcel"].sendcloud_check_cancelled_parcels()
        self.assertEqual(calls, [], msg="Sendcloud has 14 days to cancel the label")
        self.assertFalse(self._cancellation_warnings(parcel))

    def test_the_scheduled_check_warns_only_once(self):
        parcel = self._cancel_queued_return()
        parcel.sendcloud_status = "3"
        self._age_parcel(parcel, 15)
        self._patch_get_parcel(3)
        self.env["sendcloud.parcel"].sendcloud_check_cancelled_parcels()
        self._age_parcel(parcel, 15)
        self.env["sendcloud.parcel"].sendcloud_check_cancelled_parcels()
        self.assertEqual(len(self._cancellation_warnings(parcel)), 1)
