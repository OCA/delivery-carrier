# ruff: noqa: E501

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from zeep.exceptions import Fault

from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase

from odoo.addons.delivery_schenker.models.schenker_request import (
    SCHENKER_API_SERVICE,
    SCHENKER_API_URL,
    SchenkerRequest,
)


class TestSchenkerRequest(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.client_patch = patch(
            "odoo.addons.delivery_schenker.models.schenker_request.Client"
        )
        cls.settings_patch = patch(
            "odoo.addons.delivery_schenker.models.schenker_request.Settings"
        )
        cls.history_patch = patch(
            "odoo.addons.delivery_schenker.models.schenker_request.HistoryPlugin"
        )
        cls.client_mock = cls.client_patch.start()
        cls.settings_mock = cls.settings_patch.start()
        cls.history_mock = cls.history_patch.start()
        cls.addClassCleanup(cls.client_patch.stop)
        cls.addClassCleanup(cls.settings_patch.stop)
        cls.addClassCleanup(cls.history_patch.stop)

    def _new_request(self, **kwargs):
        return SchenkerRequest(self.env, access_key="access-key", **kwargs)

    def test_init_uses_selected_environment_and_service(self):
        request = self._new_request(
            group_id="group", user="user", prod=True, service="tracking"
        )

        self.assertEqual(request.access_key, "access-key")
        self.assertEqual(request.group_id, "group")
        self.assertEqual(request.user, "user")
        self.client_mock.assert_called_with(
            wsdl=SCHENKER_API_URL["prod"] + SCHENKER_API_SERVICE["tracking"],
            settings=self.settings_mock.return_value,
            plugins=[self.history_mock.return_value],
        )

    def test_process_reply_calls_services_with_positional_and_keyword_arguments(self):
        request = self._new_request()
        positional_service = MagicMock(return_value="response")
        keyword_service = MagicMock(return_value="keyword response")

        self.assertEqual(
            request._process_reply(positional_service, {"foo": "bar"}), "response"
        )
        self.assertEqual(
            request._process_reply(keyword_service, {"foo": "bar"}, send_as_kw=True),
            "keyword response",
        )
        positional_service.assert_called_once_with({"foo": "bar"})
        keyword_service.assert_called_once_with(foo="bar")

    def test_process_reply_converts_schenker_fault_to_validation_error(self):
        request = self._new_request()
        response = SimpleNamespace(
            text=(
                "<root><faultstring>Fault text</faultstring><message>Message</message>"
                "<code>CODE</code></root>"
            )
        )
        service = MagicMock(side_effect=[Fault("fault"), response])

        with self.assertRaisesRegex(ValidationError, "Fault text"):
            request._process_reply(service, {"foo": "bar"})

        request.client.settings.assert_called_once_with(raw_response=True)
        self.assertEqual(service.call_count, 2)

    def test_process_reply_reraises_unparseable_fault(self):
        request = self._new_request()
        service = MagicMock(
            side_effect=[Fault("fault"), SimpleNamespace(text="<root/>")]
        )

        with self.assertRaises(Fault):
            request._process_reply(service, {"foo": "bar"})

    def test_booking_helpers_build_expected_payloads(self):
        request = self._new_request(group_id="group", user="user")
        expected_credentials = {
            "applicationArea": {
                "accessKey": "access-key",
                "userId": "user",
                "groupId": "group",
            }
        }

        self.assertEqual(request._shipping_api_credentials(), expected_credentials)
        self.assertEqual(request._shipping_type_method("land"), "getBookingRequestLand")
        self.assertEqual(request._shipping_type_method("air"), "getBookingRequestAir")
        self.assertEqual(
            request._shipping_type_method("ocean_fcl"), "getBookingRequestOceanFCL"
        )
        self.assertEqual(
            request._shipping_type_method("ocean_lcl"), "getBookingRequestOceanLCL"
        )
        self.assertEqual(
            request._shipping_type_method("unknown"), "getBookingRequestLand"
        )
        self.assertEqual(request._scheneker_shipping_api_wrapper("land"), "bookingLand")
        self.assertEqual(request._scheneker_shipping_api_wrapper("air"), "bookingAir")
        self.assertEqual(
            request._scheneker_shipping_api_wrapper("ocean_fcl"), "bookingOceanFCL"
        )
        self.assertEqual(
            request._scheneker_shipping_api_wrapper("ocean_lcl"), "bookingOceanLCL"
        )
        self.assertEqual(request._scheneker_shipping_api_wrapper("unknown"), "land")

    def test_booking_operations_delegate_to_soap_client(self):
        request = self._new_request()
        response = SimpleNamespace(bookingId="booking", barcodeDocument="label")
        request._process_reply = MagicMock(return_value=response)
        request.client.service = MagicMock()

        shipping = request._send_shipping({"weight": 1}, "air")
        self.assertEqual(shipping, {"booking_id": "booking", "barcode": "label"})
        payload = request._process_reply.call_args.args[1]
        self.assertTrue(payload["bookingAir"]["submitBooking"])

        request._process_reply.return_value = SimpleNamespace(document="pdf")
        self.assertEqual(request._shipping_label(["booking"], "A4"), "pdf")
        label_payload = request._process_reply.call_args.args[1]
        self.assertEqual(
            label_payload["barcodeRequest"], {"format": "A4", "bookingId": ["booking"]}
        )

        request._process_reply.return_value = True
        self.assertTrue(request._cancel_shipment("booking"))
        cancel_payload = request._process_reply.call_args.args[1]
        self.assertEqual(cancel_payload["cancelRequest"], {"bookingId": "booking"})

    def test_tracking_operations_cover_empty_land_and_international_references(self):
        request = self._new_request()
        request.client.service = MagicMock()
        request._process_reply = MagicMock(
            return_value=SimpleNamespace(Shipment=["shipment"])
        )

        self.assertEqual(
            request._tracking_api_credentials(), {"AccessKey": "access-key", "in": {}}
        )
        self.assertEqual(request._get_tracking_states(), {})
        self.assertEqual(
            request._get_tracking_states("booking", booking_type="land"),
            {"shipment": ["shipment"]},
        )
        payload = request._process_reply.call_args.args[1]
        self.assertEqual(payload["in"]["transportNature"], "exp")
        self.assertEqual(
            request._get_tracking_states(
                "booking", reference_type="xx", booking_type="air"
            ),
            {"shipment": ["shipment"]},
        )
        payload = request._process_reply.call_args.args[1]
        self.assertEqual(payload["in"]["referenceType"], "xx")
        self.assertEqual(payload["in"]["transportNature"], "int")
