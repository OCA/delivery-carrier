# Copyright 2020 Hunki Enterprises BV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import json
from contextlib import contextmanager
from functools import partial
from unittest.mock import Mock, patch

import zeep
from werkzeug.exceptions import Forbidden, NotFound, Unauthorized
from werkzeug.test import EnvironBuilder
from werkzeug.wrappers import Request as WerkzeugRequest

from odoo import http
from odoo.exceptions import UserError

from odoo.addons.base_delivery_carrier_label.tests import carrier_label_case


class DeliveryCarrierLabelPaazlCase(carrier_label_case.CarrierLabelCase):
    def setUp(self):
        super().setUp()
        self.odoo_root = http.Root()
        self.session = self.odoo_root.session_store.new()

    def _create_account(self):
        return self.env["carrier.account"].create(
            {
                "name": "Paazl account",
                "delivery_type": "paazl",
                "account": "webshop id",
                "password": "integration password",
                "paazl_bearer_token": "bearer token",
            }
        )

    def _create_order_picking(self):
        self._create_account()
        super()._create_order_picking()

    def _transfer_order_picking(self):
        with self._setup_mock_client() as mock_client:
            super()._transfer_order_picking()
            self.assertTrue(
                mock_client.service.order.call_args[1]["products"]["product"],
                "No products were sent",
            )
            call_args = mock_client.service.order.call_args
        return call_args

    @contextmanager
    def _setup_mock_client(self):
        mock_client = Mock()
        mock_client.service.order.return_value = Mock(error=False)
        mock_client.service.commitOrder.return_value = Mock(error=False)
        mock_client.service.changeOrder.return_value = Mock(error=False)
        mock_client.service.generateLabels.return_value = Mock(
            error=False, labels=b"hello world", metaData=[{"trackingNumber": "number"}],
        )
        with patch.object(zeep, "Client") as mock_client_class:
            mock_client_class.return_value = mock_client
            yield mock_client

    def _picking_data(self):
        return {
            "option_ids": [
                (
                    4,
                    self.env["delivery.carrier.option"]
                    .create(
                        {
                            "tmpl_option_id": self.env.ref(
                                "delivery_carrier_label_paazl.carrier_postnl_0_0_0"
                            ).id,
                        }
                    )
                    .id,
                ),
            ]
        }

    def _get_carrier(self):
        return self.env.ref("delivery_carrier_label_paazl.carrier_paazl")

    @contextmanager
    def _request(self, path, method="POST", data=None, headers=None):
        """yield request, endpoint for given http request data."""
        werkzeug_env = EnvironBuilder(
            method=method,
            path=path,
            data=data,
            headers=[
                ("cookie", "session_id=%s" % self.session.sid),
                ("content-type", "application/json"),
            ]
            + (headers or []),
            environ_base={"HTTP_HOST": "localhost", "REMOTE_ADDR": "127.0.0.1"},
        ).get_environ()
        werkzeug_request = WerkzeugRequest(werkzeug_env)
        self.odoo_root.setup_session(werkzeug_request)
        werkzeug_request.session.db = self.env.cr.dbname
        self.odoo_root.setup_db(werkzeug_request)
        self.odoo_root.setup_lang(werkzeug_request)

        request = self.odoo_root.get_request(werkzeug_request)
        request._env = self.env
        with request:
            routing_map = self.env["ir.http"].routing_map()
            endpoint, dummy = routing_map.bind_to_environ(werkzeug_env).match(
                return_rule=False,
            )
            yield request, partial(endpoint, **request.params)


class TestDeliveryCarrierLabelPaazl(
        DeliveryCarrierLabelPaazlCase,
        carrier_label_case.TestCarrierLabel):
    def test_cancel_shipment(self):
        self.assertTrue(self.picking.carrier_tracking_ref)
        with self._setup_mock_client() as mock_client:
            mock_client.service.cancelShipments.return_value = Mock(
                error=Mock(code=42, message="")
            )
            with self.assertRaises(UserError):
                self.picking.carrier_id.cancel_shipment(self.picking)
            mock_client.service.cancelShipments.return_value = Mock(error=False)
            self.picking.cancel_shipment()
            self.assertFalse(self.picking.carrier_tracking_ref)

    def test_push_api(self):
        """Test we can receive status updates from paazl"""
        # no configured account, no input
        with self._request("/_paazl/push_api/v1", data=json.dumps({})) as (
            request,
            endpoint,
        ):
            with self.assertRaises(Unauthorized):
                endpoint()

        account = self._create_account()
        headers = [
            ("Authorization", "Bearer %s" % account.paazl_bearer_token),
        ]
        request_data = {
            "webshop": account.account,
            "status": "CREATED",
            "trackTraceURL": "https://hello.world",
            "orderReference": self.picking.name,
        }

        # wrong webshop
        with self._request(
            "/_paazl/push_api/v1",
            data=json.dumps(dict(request_data, webshop="unknown")),
            headers=headers,
        ) as (request, endpoint):
            with self.assertRaises(Forbidden):
                endpoint()

        # wrong order name
        with self._request(
            "/_paazl/push_api/v1",
            data=json.dumps(dict(request_data, orderReference="unknown")),
            headers=headers,
        ) as (request, endpoint):
            with self.assertRaises(NotFound):
                endpoint()

        # happy flow
        with self._request(
            "/_paazl/push_api/v1", data=json.dumps(request_data), headers=headers
        ) as (request, endpoint):
            messages_before = self.picking.message_ids
            endpoint()
            self.assertEqual(
                self.picking.carrier_tracking_url, request_data["trackTraceURL"]
            )
            self.assertTrue(self.picking.message_ids - messages_before)

    def test_change_order(self):
        """Test change order in paazl"""
        self.assertTrue(self.picking.carrier_tracking_ref)
        with self._setup_mock_client() as mock_client:
            mock_client.service.commitOrder.return_value = Mock(
                error=Mock(code=1003, message="")
            )
            self.picking._paazl_send_update_order(change_order=True)
            self.assertTrue(self.picking.carrier_tracking_ref)


class TestDeliveryCarrierLabelPaazlPackaging(TestDeliveryCarrierLabelPaazl):
    def _picking_data(self):
        self.picking.move_line_ids.write({'qty_done': 1})
        self.picking._put_in_pack()
        self.picking.package_ids.packaging_id = self.env[
            "product.packaging"].create({
                'name': 'Test',
                'width': 42,
                'height': 42,
                'length': 42,
            })
        return super()._picking_data()
