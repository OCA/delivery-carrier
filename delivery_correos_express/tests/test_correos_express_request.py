# Copyright 2025 Studio73 - Pablo Cortés <pablo.cortes@studio73.es>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from unittest import mock

import requests

from odoo.exceptions import UserError
from odoo.tests import common

from odoo.addons.delivery_correos_express.models.correos_express_request import (
    CorreosExpressRequest,
)

request_model = (
    "odoo.addons.delivery_correos_express.models."
    "correos_express_request.CorreosExpressRequest"
)


class TestCorreosExpressRequest(common.SingleTransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.shipping_product = cls.env["product.product"].create(
            {"type": "service", "name": "Test Shipping Product", "list_price": 10}
        )
        cls.carrier_correos_express = cls.env["delivery.carrier"].create(
            {
                "name": "Correos Express",
                "delivery_type": "correos_express",
                "correos_express_username": "test_user",
                "correos_express_password": "test_password",
                "product_id": cls.shipping_product.id,
            }
        )

        cls.correos_express_request = CorreosExpressRequest(cls.carrier_correos_express)

    @mock.patch("requests.post")
    def test_01_send_api_request_success(self, mock_post):
        mock_post.return_value.json.return_value = {
            "codigoRetorno": 0,
            "mensajeRetorno": "OK",
        }
        mock_post.return_value.raise_for_status.return_value = None
        response = self.correos_express_request._send_api_request(
            "POST", "https://test.url", data={"test": "data"}
        )
        self.assertEqual(response.json(), {"codigoRetorno": 0, "mensajeRetorno": "OK"})

    @mock.patch("requests.post")
    def test_02_send_api_request_timeout(self, mock_post):
        self.env = self.env(context=dict(self.env.context, lang="en_US"))
        mock_post.side_effect = requests.exceptions.Timeout()
        with self.assertRaises(UserError):
            self.correos_express_request._send_api_request(
                "POST", "https://test.url", data={"test": "data"}
            )

    @mock.patch("requests.post")
    def test_03_send_api_request_error(self, mock_post):
        mock_post.side_effect = Exception("Test Error")
        with self.assertRaises(UserError):
            self.correos_express_request._send_api_request(
                "POST", "https://test.url", data={"test": "data"}
            )

    def test_04_check_for_error_shipment_success(self):
        result = {"codigoRetorno": 0, "mensajeRetorno": ""}
        return_code, message = self.correos_express_request._check_for_error(result)
        self.assertEqual(return_code, 0)
        self.assertEqual(message, "")

    def test_04_check_for_error_shipment_error(self):
        result = {"codigoRetorno": 1, "mensajeRetorno": "Test Error"}
        return_code, message = self.correos_express_request._check_for_error(result)
        self.assertEqual(return_code, 1)
        self.assertEqual(message, "Test Error")

    def test_05_check_for_error_label_success(self):
        result = {"codErr": 0, "desErr": ""}
        return_code, message = self.correos_express_request._check_for_error(result)
        self.assertEqual(return_code, 0)
        self.assertEqual(message, "")

    def test_06_check_for_error_label_error(self):
        result = {"codErr": 1, "desErr": "Test Error"}
        return_code, message = self.correos_express_request._check_for_error(result)
        self.assertEqual(return_code, 1)
        self.assertEqual(message, "Test Error")

    def test_07_check_for_error_tracking_success(self):
        result = {"error": 0, "mensajeError": ""}
        return_code, message = self.correos_express_request._check_for_error(result)
        self.assertEqual(return_code, 0)
        self.assertEqual(message, "")

    def test_08_check_for_error_tracking_error(self):
        result = {"error": 1, "mensajeError": "Test Error"}
        return_code, message = self.correos_express_request._check_for_error(result)
        self.assertEqual(return_code, 1)
        self.assertEqual(message, "Test Error")

    def test_check_for_error_no_error_codes(self):
        result = {}
        return_code, message = self.correos_express_request._check_for_error(result)
        self.assertEqual(return_code, 999)
        self.assertEqual(message, "Webservice ERROR.")
