# Copyright 2022 FactorLibre - Jorge Martínez <jorge.martinez@factorlibre.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import json
import urllib
from unittest import mock

import requests

from odoo.exceptions import UserError
from odoo.tests import common

from ..models.deliverea_request import DelivereaRequest
from .carrier_labels_data import LABEL_1_1, LABEL_1_2
from .carrier_services_data import (
    CARRIER_LIST,
    DHL_DETAILS,
    DHL_SERVICES,
    GLS_DETAILS,
    GLS_SERVICES,
    TIPSA_DETAILS,
    TIPSA_SERVICES,
)

request_model = (
    "odoo.addons.delivery_deliverea.models.deliverea_request.DelivereaRequest"
)


class MockResponse(object):
    def __init__(self, resp_data, code=200, msg="OK", **kwargs):
        self.resp_data = resp_data
        self.content = resp_data
        self.status_code = code
        self.msg = msg
        self.ok = kwargs.get("ok", True)
        self.headers = kwargs.get("headers", {})

    def raise_for_status(self):
        if self.status_code != 200:
            raise urllib.error.HTTPError(
                "", self.status_code, str(self.status_code), None, None
            )

    def read(self):
        # pylint: disable=method-required-super
        return self.resp_data

    def getcode(self):
        return self.code

    def json(self):
        return self.resp_data

    @property
    def text(self):
        return json.dumps(self.resp_data)


class TestDeliverea(common.TransactionCase):
    def setUp(self):
        super().setUp()
        self.shipping_product = self.env.ref("delivery.product_product_local_delivery")
        distribution_center = self.env["deliverea.distribution.center"].create(
            {
                "name": "Default Distribution Center",
                "uuid": "123",
            }
        )
        self.carrier = self.env["delivery.carrier"].create(
            {
                "name": "Deliverea",
                "delivery_type": "deliverea",
                "product_id": self.shipping_product.id,
                "deliverea_username": "Test",
                "deliverea_password": "Test",
                "deliverea_distribution_center_id": distribution_center.id,
                "deliverea_url_prod": "https://preapi.deliverea.com/v3/",
                "deliverea_url_test": "https://preapi.deliverea.com/v3/",
                "deliverea_default_packaging_id": self.env.ref(
                    "delivery_deliverea.stock_package_deliverea_default"
                ).id,
                "deliverea_description": "Description",
            }
        )
        self.carrier.deliverea_note_selection_id = self.env["ir.model.fields"].search(
            [("model", "=", "stock.picking"), ("name", "=", "note")]
        )
        self.service = self.env["carrier.deliverea.service"].create(
            {
                "name": "Standard",
                "code": "standard",
                "description": "Standard",
                "carrier_id": [(4, self.carrier.id)],
            }
        )
        self.product = self.env["product.product"].create(
            {"name": "Test Product", "type": "product"}
        )
        self.partner = self.env["res.partner"].create(
            {
                "name": "Test Partner",
                "street": "Street 1",
                "street2": "Street 2",
                "zip": "28035",
                "city": "Madrid",
                "country_id": self.env.ref("base.es").id,
                "state_id": self.env.ref("base.state_es_m").id,
                "phone": "123456789",
                "email": "test@test.com",
            }
        )
        self.stock_location = self.env.ref("stock.stock_location_stock")
        self.customer_location = self.env.ref("stock.stock_location_customers")
        self.picking = self.env["stock.picking"].create(
            {
                "name": "Test Picking",
                "partner_id": self.partner.id,
                "move_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "product_uom_qty": 1,
                            "product_uom": self.product.uom_id.id,
                            "name": self.product.name,
                            "location_id": self.stock_location.id,
                            "location_dest_id": self.customer_location.id,
                        },
                    )
                ],
                "location_id": self.stock_location.id,
                "location_dest_id": self.customer_location.id,
                "picking_type_id": self.env.ref("stock.picking_type_out").id,
                "carrier_id": self.carrier.id,
                "number_of_packages": 2,
            }
        )
        self.env["stock.quant"].create(
            {
                "product_id": self.product.id,
                "location_id": self.stock_location.id,
                "quantity": 1,
            }
        )
        self.picking.action_assign()

    def test_00_get_services(self):
        def _call_side_effect(*args, **kwargs):
            if "integrations" in kwargs.get("url"):
                if "dhl" in kwargs.get("url"):
                    return MockResponse(DHL_SERVICES, code=200)
                if "gls" in kwargs.get("url"):
                    return MockResponse(GLS_SERVICES, code=200)
                if "tipsa" in kwargs.get("url"):
                    return MockResponse(TIPSA_SERVICES, code=200)
            elif "cost-centers" in kwargs.get("url"):
                if "dhl" in kwargs.get("url"):
                    return MockResponse(DHL_DETAILS, code=200)
                if "gls" in kwargs.get("url"):
                    return MockResponse(GLS_DETAILS, code=200)
                if "tipsa" in kwargs.get("url"):
                    return MockResponse(TIPSA_DETAILS, code=200)
            elif "carriers" in kwargs.get("url"):
                return MockResponse(CARRIER_LIST, code=200)

        mock_call = mock.MagicMock(side_effect=_call_side_effect)
        with mock.patch.object(requests, "get", new=mock_call):
            self.carrier.deliverea_get_services()
            self.assertEqual(
                self.env["carrier.deliverea.service"].search(
                    [("carrier_code", "!=", False)], count=True
                ),
                17,
            )
            self.assertEqual(
                self.env["carrier.deliverea.service"].search(
                    [("carrier_code", "!=", False), ("active", "=", False)],
                    count=True,
                ),
                0,
            )
            self.assertNotEqual(
                self.env["carrier.deliverea.service"]
                .search(
                    [("carrier_code", "!=", False), ("active", "=", False)],
                    limit=1,
                )
                .code,
                "time-definite-national",
            )

    def test_01_create_order(self):
        create_shipment_value = {
            "delivereaReference": "Sbe2fd53e94869d",
            "carrierCode": "dummy",
            "serviceCode": "standard",
            "costCenterCode": "DEFAULT",
        }
        get_shipment_tracking_value = [
            {
                "code": "01",
                "message": "Pedido en preparación",
                "carrierCode": None,
                "category": "documented",
                "carrierMessage": None,
                "occurredAt": "2021-01-02T13:00:54+0100",
                "receivedAt": "2021-01-02T13:00:54+0100",
            },
            {
                "code": "11",
                "message": "Recogido",
                "carrierCode": None,
                "category": "documented",
                "carrierMessage": None,
                "occurredAt": "2021-01-03T13:00:54+0100",
                "receivedAt": "2021-01-03T13:00:54+0100",
            },
        ]

        def _call_side_effect(*args, **kwargs):
            if "label" in kwargs.get("url"):
                return MockResponse(LABEL_1_1, code=200)
            elif "trackings" in kwargs.get("url"):
                return MockResponse(get_shipment_tracking_value, code=200)

        mock_call = mock.MagicMock(side_effect=_call_side_effect)
        requests_create_shipment = mock.MagicMock(
            return_value=MockResponse(create_shipment_value, code=200)
        )
        with mock.patch.object(requests, "post", new=requests_create_shipment):
            with mock.patch.object(requests, "get", new=mock_call):
                self.carrier.deliverea_send_shipping(self.picking)
                self.assertEqual(
                    self.picking.deliverea_reference,
                    "Sbe2fd53e94869d",
                )

    def test_02_create_order_mandatory_field(self):
        self.partner.zip = False
        with self.assertRaises(UserError) as e:
            self.carrier.deliverea_send_shipping(self.picking)
        self.assertEqual(
            "The value for zipCode field/s is mandatory in Test Partner",
            e.exception.args[0],
        )

    def test_03_get_label(self):
        get_shipment_tracking_value = [
            {
                "code": "01",
                "message": "Pedido en preparación",
                "carrierCode": None,
                "category": "documented",
                "carrierMessage": None,
                "occurredAt": "2021-01-02T13:00:54+0100",
                "receivedAt": "2021-01-02T13:00:54+0100",
            },
            {
                "code": "11",
                "message": "Recogido",
                "carrierCode": None,
                "category": "documented",
                "carrierMessage": None,
                "occurredAt": "2021-01-03T13:00:54+0100",
                "receivedAt": "2021-01-03T13:00:54+0100",
            },
        ]

        def _call_side_effect(*args, **kwargs):
            if "label" in kwargs.get("url"):
                return MockResponse(LABEL_1_2, code=200)
            elif "trackings" in kwargs.get("url"):
                return MockResponse(get_shipment_tracking_value, code=200)

        mock_call = mock.MagicMock(side_effect=_call_side_effect)

        with mock.patch.object(requests, "get", new=mock_call):
            self.picking.deliverea_reference = "Secb189a5d61d32"
            self.picking.deliverea_parcel_client_code = "0001,0002"
            self.carrier.deliverea_get_label(self.picking)
            attachment = self.env["ir.attachment"].search(
                [
                    ("res_model", "=", "stock.picking"),
                    ("res_id", "=", self.picking.id),
                ]
            )
        self.assertTrue(attachment)

    def test_04_create_return_and_delete(self):
        return_value = {
            "delivereaReference": "Sbe2fd53e94869d",
            "carrierCode": "dummy",
            "serviceCode": "standard",
            "costCenterCode": "DEFAULT",
        }
        requests_mock_call = mock.MagicMock(
            return_value=MockResponse(return_value, code=200)
        )
        with mock.patch.object(requests, "post", new=requests_mock_call):
            self.carrier.deliverea_return_shipping(self.picking)
            self.assertEqual(
                self.picking.deliverea_reference,
                "Sbe2fd53e94869d",
            )
        requests_mock_call = mock.MagicMock(
            return_value=MockResponse("DELETE", code=200)
        )
        with mock.patch.object(requests, "delete", new=requests_mock_call):
            self.carrier.deliverea_cancel_shipment(self.picking)
        requests_mock_call.assert_called()

    def test_05_get_tracking_shipment(self):
        return_value = [
            {
                "code": "01",
                "message": "Pedido en preparación",
                "carrierCode": None,
                "category": "documented",
                "carrierMessage": None,
                "occurredAt": "2021-01-02T13:00:54+0100",
                "receivedAt": "2021-01-02T13:00:54+0100",
            },
            {
                "code": "11",
                "message": "Recogido",
                "carrierCode": None,
                "category": "documented",
                "carrierMessage": None,
                "occurredAt": "2021-01-03T13:00:54+0100",
                "receivedAt": "2021-01-03T13:00:54+0100",
            },
        ]
        requests_mock_call = mock.MagicMock(
            return_value=MockResponse(return_value, code=200)
        )
        with mock.patch.object(requests, "get", new=requests_mock_call):
            self.carrier.deliverea_tracking_state_update(self.picking)
            self.assertEqual(self.picking.tracking_state, False)
            self.assertEqual(self.picking.tracking_state_history, False)
            self.picking.deliverea_reference = "Sbe2fd53e94869d"
            self.carrier.deliverea_tracking_state_update(self.picking)
            self.assertEqual(self.picking.tracking_state, "[11] Recogido")
            self.assertEqual(
                self.picking.tracking_state_history,
                "- 2021-01-02T13:00:54+0100: [01] Pedido en preparación\n"
                "- 2021-01-03T13:00:54+0100: [11] Recogido",
            )
            self.assertEqual(self.picking.delivery_state, "customer_delivered")
            self.assertTrue(self.picking.date_delivered)

    def test_06_create_return(self):
        return_value = {
            "delivereaReference": "Sbe2fd53e94869d",
            "carrierCode": "dummy",
            "serviceCode": "standard",
            "costCenterCode": "DEFAULT",
        }
        requests_mock_call = mock.MagicMock(
            return_value=MockResponse(return_value, code=200)
        )
        with mock.patch.object(requests, "post", new=requests_mock_call):
            self.carrier.deliverea_return_shipping(self.picking)
            self.assertEqual(
                self.picking.deliverea_reference,
                "Sbe2fd53e94869d",
            )
        requests_mock_call = mock.MagicMock(
            return_value=MockResponse("DELETE", code=200)
        )
        with mock.patch.object(requests, "delete", new=requests_mock_call):
            self.carrier.deliverea_cancel_shipment(self.picking)
        requests_mock_call.assert_called()

    def test_07_get_exception(self):
        with self.assertRaises(UserError):
            DelivereaRequest._send_api_request(
                DelivereaRequest, request_type="TEST", url="TEST", skip_auth=True
            )

    def test_08_get_exception(self):
        requests_mock_call = mock.MagicMock(return_value=MockResponse("Test", code=202))
        with mock.patch.object(requests, "get", new=requests_mock_call):
            res = DelivereaRequest._send_api_request(
                DelivereaRequest, request_type="GET", url="TEST", skip_auth=True
            )
            self.assertTrue(res)

    def test_9_get_exception(self):
        requests_mock_call = mock.MagicMock(
            return_value=MockResponse(
                {
                    "error": {
                        "code": "error_code",
                        "message": "code_message",
                        "detail": "error_detail",
                    }
                },
                code=300,
            )
        )
        with mock.patch.object(requests, "get", new=requests_mock_call):
            with mock.patch.object(
                DelivereaRequest, "_check_error", return_value=True
            ) as mock_error:
                DelivereaRequest._send_api_request(
                    DelivereaRequest, request_type="GET", url="TEST", skip_auth=True
                )
        mock_error.assert_called()

    def test_10_get_exception(self):
        return_value = {
            "error": {
                "code": "error_code",
                "message": "code_message",
                "detail": "error_detail",
            }
        }
        with self.assertRaises(UserError):
            DelivereaRequest._check_error(DelivereaRequest, return_value)

    def test_11_get_exception(self):
        return_value = {"Error test": "Error"}
        with self.assertRaises(UserError):
            DelivereaRequest._check_error(DelivereaRequest, return_value)
