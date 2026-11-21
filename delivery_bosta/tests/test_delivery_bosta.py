# Copyright 2026 Yahia Sherif
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import json
from unittest.mock import Mock, patch

import requests

from odoo.exceptions import UserError
from odoo.tests import HttpCase, TransactionCase, tagged

POST = "odoo.addons.delivery_bosta.models.delivery_carrier.requests.post"


def bosta_response(status, body):
    return Mock(
        ok=status < 400,
        status_code=status,
        text=json.dumps(body),
        json=Mock(return_value=body),
    )


def created(tracking_number=48089608):
    return bosta_response(
        200,
        {"success": True, "data": {"_id": "6650f0", "trackingNumber": tracking_number}},
    )


class BostaSetup:
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.carrier = cls.env["delivery.carrier"].create(
            {
                "name": "Bosta",
                "delivery_type": "bosta",
                "product_id": cls.env["product.product"]
                .create(
                    {"name": "Bosta Delivery", "type": "service", "list_price": 60.0}
                )
                .id,
                "bosta_api_key": "test-api-key",
                "bosta_webhook_secret": "hook-secret",
            }
        )
        cls.partner = cls.env["res.partner"].create(
            {
                "name": "Mona Adel Hassan",
                "street": "12 Tahrir Street",
                "street2": "Apartment 4",
                "city": "Downtown",
                "state_id": cls.env.ref("base.state_eg_c").id,
                "country_id": cls.env.ref("base.eg").id,
                "phone": "+201000000000",
                "email": "mona@example.com",
            }
        )
        cls.lamp = cls.env["product.product"].create(
            {"name": "Desk Lamp", "type": "consu", "list_price": 450.0}
        )


@tagged("post_install", "-at_install")
class TestBostaShipping(BostaSetup, TransactionCase):
    def setUp(self):
        super().setUp()
        self.order = self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "order_line": [
                    (0, 0, {"product_id": self.lamp.id, "product_uom_qty": 2})
                ],
            }
        )
        self.order.set_delivery_line(self.carrier, 60.0)
        self.order.action_confirm()
        self.picking = self.order.picking_ids

    def send(self, picking=None, response=None):
        with patch(POST, return_value=response or created()) as post:
            result = self.carrier.send_shipping(picking or self.picking)
        return result, post

    def pay_cash_on_delivery(self):
        provider = self.env["payment.provider"].create(
            {
                "name": "Cash on Delivery",
                "code": "custom",
                "custom_mode": "cash_on_delivery",
            }
        )
        self.env["payment.transaction"].create(
            {
                "provider_id": provider.id,
                "payment_method_id": self.env.ref("payment.payment_method_unknown").id,
                "reference": "COD-TEST-1",
                "amount": self.order.amount_total,
                "currency_id": self.order.currency_id.id,
                "partner_id": self.partner.id,
                "sale_order_ids": [(6, 0, self.order.ids)],
            }
        )

    def test_creates_bosta_delivery_and_returns_tracking_number(self):
        result, post = self.send()

        self.assertEqual(result, [{"exact_price": 60.0, "tracking_number": "48089608"}])
        self.assertEqual(
            post.call_args.args[0],
            "https://app.bosta.co/api/v2/deliveries?apiVersion=1",
        )
        self.assertEqual(
            post.call_args.kwargs["headers"], {"Authorization": "test-api-key"}
        )
        payload = post.call_args.kwargs["json"]
        self.assertEqual(payload["type"], 10)
        self.assertEqual(
            payload["specs"]["packageDetails"],
            {"itemsCount": 2, "description": "Desk Lamp"},
        )
        self.assertEqual(
            payload["dropOffAddress"],
            {
                "city": "Cairo",
                "firstLine": "12 Tahrir Street",
                "secondLine": "Apartment 4",
            },
        )
        self.assertEqual(
            payload["receiver"],
            {
                "firstName": "Mona",
                "lastName": "Adel Hassan",
                "phone": "+201000000000",
                "email": "mona@example.com",
            },
        )
        self.assertEqual(
            payload["businessReference"], f"{self.order.name} {self.picking.name}"
        )
        self.assertTrue(payload["webhookUrl"].endswith("/delivery_bosta/webhook"))
        self.assertEqual(
            payload["webhookCustomHeaders"], {"Authorization": "hook-secret"}
        )
        self.assertNotIn("cod", payload)

    def test_api_url_can_point_to_another_bosta_environment(self):
        self.env["ir.config_parameter"].sudo().set_param(
            "delivery_bosta.api_url", "http://bosta-mock:8080/api/v2"
        )

        _result, post = self.send()

        self.assertEqual(
            post.call_args.args[0],
            "http://bosta-mock:8080/api/v2/deliveries?apiVersion=1",
        )

    def test_collects_order_total_when_paid_cash_on_delivery(self):
        self.pay_cash_on_delivery()

        _result, post = self.send()

        self.assertEqual(post.call_args.kwargs["json"]["cod"], self.order.amount_total)
        self.assertEqual(self.picking.bosta_cod_amount, self.order.amount_total)

    def test_backorder_does_not_collect_cash_twice(self):
        self.pay_cash_on_delivery()
        self.send()
        backorder = self.picking.copy()
        backorder.sale_id = self.order

        _result, post = self.send(backorder, created(48089609))

        self.assertNotIn("cod", post.call_args.kwargs["json"])

    def test_send_to_shipper_stores_tracking_reference_on_transfer(self):
        with patch(POST, return_value=created("777")):
            self.picking.send_to_shipper()

        self.assertEqual(self.picking.carrier_tracking_ref, "777")
        self.assertEqual(self.picking.delivery_state, "shipping_recorded_in_carrier")
        self.assertEqual(
            self.carrier.get_tracking_link(self.picking),
            "https://bosta.co/en-eg/tracking-shipments?shipment-number=777",
        )

    def test_several_tracking_numbers_get_one_link_each(self):
        self.picking.carrier_tracking_ref = "777,888"

        links = json.loads(self.carrier.get_tracking_link(self.picking))

        self.assertEqual([ref for ref, _url in links], ["777", "888"])
        self.assertTrue(links[1][1].endswith("shipment-number=888"))

    def test_incomplete_address_is_refused_before_calling_bosta(self):
        self.partner.write({"street": "12", "phone": False})

        with (
            patch(POST) as post,
            self.assertRaisesRegex(
                UserError, r"street \(more than 5 characters\), phone"
            ),
        ):
            self.carrier.send_shipping(self.picking)
        post.assert_not_called()

    def test_bosta_error_message_is_shown_to_the_user(self):
        with self.assertRaisesRegex(UserError, r"HTTP 400\): City Not Found"):
            self.send(
                response=bosta_response(
                    400, {"success": False, "message": "City Not Found"}
                )
            )

    def test_timeout_warns_that_the_delivery_may_exist(self):
        with (
            patch(POST, side_effect=requests.Timeout()),
            self.assertRaisesRegex(
                UserError, f"may still have created the delivery.*{self.picking.name}"
            ),
        ):
            self.carrier.send_shipping(self.picking)
        self.assertFalse(self.picking.bosta_cod_amount)

    def test_debug_log_never_contains_credentials(self):
        with patch.object(type(self.carrier), "log_xml") as log:
            self.send()

        logged = " ".join(str(call.args[0]) for call in log.call_args_list)
        self.assertIn("12 Tahrir Street", logged)
        self.assertNotIn("hook-secret", logged)
        self.assertNotIn("test-api-key", logged)

    def test_missing_api_key_is_refused(self):
        self.carrier.bosta_api_key = False

        with (
            patch(POST) as post,
            self.assertRaisesRegex(UserError, "Set the Bosta API key"),
        ):
            self.carrier.send_shipping(self.picking)
        post.assert_not_called()

    def test_cancel_points_to_the_bosta_dashboard(self):
        with self.assertRaisesRegex(UserError, "Bosta dashboard"):
            self.carrier.cancel_shipment(self.picking)


@tagged("post_install", "-at_install")
class TestBostaWebhook(BostaSetup, HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.picking = cls.env["stock.picking"].create(
            {
                "picking_type_id": cls.env.ref("stock.picking_type_out").id,
                "partner_id": cls.partner.id,
                "carrier_id": cls.carrier.id,
                "carrier_tracking_ref": "48089608",
            }
        )

    def post_update(self, body, secret="hook-secret"):
        response = self.url_open(
            "/delivery_bosta/webhook",
            data=body if isinstance(body, str) else json.dumps(body),
            headers={"Content-Type": "application/json", "Authorization": secret},
        )
        self.picking.invalidate_recordset()
        return response

    def test_status_update_is_recorded_on_the_transfer(self):
        response = self.post_update(
            {"trackingNumber": 48089608, "state": 45, "timeStamp": 1763700000000}
        )

        self.assertEqual(response.json(), {"status": "ok"})
        self.assertEqual(self.picking.tracking_state, "Delivered")
        self.assertEqual(self.picking.delivery_state, "customer_delivered")
        self.assertTrue(self.picking.date_delivered)
        self.assertIn("Delivered", self.picking.tracking_state_history)
        self.assertEqual(self.picking.bosta_tracking_timestamp, 1763700000000)
        update = self.picking.message_ids.filtered(
            lambda m: "Delivered" in m.tracking_value_ids.mapped("new_value_char")
        )
        self.assertEqual(update.author_id, self.env.ref("base.partner_root"))

    def test_bosta_states_map_to_carrier_states(self):
        for stamp, (code, carrier_state) in enumerate(
            [
                (24, "in_transit"),
                (47, "incident"),
                (46, "warehouse_delivered"),
                (49, "canceled_shipment"),
            ],
            start=1,
        ):
            self.post_update(
                {"trackingNumber": "48089608", "state": code, "timeStamp": stamp}
            )
            self.assertEqual(self.picking.delivery_state, carrier_state)
        self.assertEqual(len(self.picking.tracking_state_history.splitlines()), 4)

    def test_repeated_update_adds_no_second_chatter_entry(self):
        self.post_update({"trackingNumber": "48089608", "state": 24, "timeStamp": 1000})
        messages = len(self.picking.message_ids)

        self.post_update({"trackingNumber": "48089608", "state": 24, "timeStamp": 1000})

        self.assertEqual(self.picking.tracking_state, "Received at warehouse")
        self.assertEqual(len(self.picking.message_ids), messages)
        self.assertEqual(len(self.picking.tracking_state_history.splitlines()), 1)

    def test_older_or_replayed_update_does_not_overwrite_a_newer_one(self):
        self.post_update({"trackingNumber": "48089608", "state": 45, "timeStamp": 2000})

        response = self.post_update(
            {"trackingNumber": "48089608", "state": 21, "timeStamp": 1000}
        )

        self.assertEqual(response.json(), {"status": "unchanged"})
        self.assertEqual(self.picking.tracking_state, "Delivered")
        self.assertEqual(self.picking.delivery_state, "customer_delivered")

    def test_transfer_with_several_tracking_numbers_is_found(self):
        self.picking.carrier_tracking_ref = "111,48089608"

        self.post_update({"trackingNumber": "48089608", "state": 45})

        self.assertEqual(self.picking.tracking_state, "Delivered")

    def test_unknown_state_code_is_kept_verbatim(self):
        self.post_update({"trackingNumber": "48089608", "state": 999})

        self.assertEqual(self.picking.tracking_state, "State 999")
        self.assertFalse(self.picking.delivery_state)

    def test_wrong_secret_is_rejected(self):
        response = self.post_update(
            {"trackingNumber": "48089608", "state": 45}, secret="guess"
        )

        self.assertEqual(response.status_code, 401)
        self.assertFalse(self.picking.tracking_state)

    def test_wrong_secret_does_not_reveal_whether_a_delivery_exists(self):
        response = self.post_update(
            {"trackingNumber": "123", "state": 45}, secret="guess"
        )

        self.assertEqual(response.status_code, 401)

    def test_one_carrier_secret_cannot_update_another_carriers_delivery(self):
        self.carrier.copy(
            {"name": "Bosta Alexandria", "bosta_webhook_secret": "other-secret"}
        )

        response = self.post_update(
            {"trackingNumber": "48089608", "state": 45}, secret="other-secret"
        )

        self.assertEqual(response.json(), {"status": "ignored"})
        self.assertFalse(self.picking.tracking_state)

    def test_update_for_unknown_delivery_is_ignored(self):
        response = self.post_update({"trackingNumber": "123", "state": 45})

        self.assertEqual(response.json(), {"status": "ignored"})

    def test_malformed_body_is_rejected(self):
        response = self.post_update("not json")

        self.assertEqual(response.status_code, 400)

    def test_oversized_body_is_rejected(self):
        response = self.post_update(
            {"trackingNumber": "48089608", "state": 45, "padding": "x" * 70000}
        )

        self.assertEqual(response.status_code, 413)
        self.assertFalse(self.picking.tracking_state)
