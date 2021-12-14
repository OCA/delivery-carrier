# Copyright 2021 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging
from xml.etree import ElementTree as ET

from zeep import Client, Settings
from zeep.exceptions import Fault
from zeep.plugins import HistoryPlugin

from odoo import _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

SCHENKER_API_URL = {
    "test": "https://eschenker-fat.dbschenker.com",
    "prod": "https://eschenker.dbschenker.com",
}
SCHENKER_API_SERVICE = {
    "booking": "/webservice/bookingWebServiceV1_1?wsdl",
    "tracking": "/webservice/trackingWebServiceV2?wsdl",
}


class SchenkerRequest:
    """Interface between Schenker SOAP API and Odoo recordset
    Abstract Schenker API Operations to connect them with Odoo

    Not all the features are implemented, but could be easily extended with
    the provided API. We leave the operations empty for future.
    """

    def __init__(
        self, access_key=None, group_id=None, user=None, prod=False, service="booking"
    ):
        self.access_key = access_key or ""
        self.group_id = group_id or ""
        self.user = user or ""
        self.service = service
        api_env = "prod" if prod else "test"
        self.history = HistoryPlugin(maxlen=10)
        settings = Settings(strict=False, xml_huge_tree=True)
        self.client = Client(
            wsdl=SCHENKER_API_URL[api_env] + SCHENKER_API_SERVICE[service],
            settings=settings,
            plugins=[self.history],
        )

    def _process_reply(self, service, vals=None, send_as_kw=False):
        """Schenker API returns error petitions as server exceptions wich makes zeep to
        raise a Fault exception as well. To catch the error info we need to make a
        raw_response request and the extract the error codes from the response."""
        try:
            if not send_as_kw:
                response = service(vals)
            else:
                response = service(**vals)
        except Fault as e:
            with self.client.settings(raw_response=True):
                if not send_as_kw:
                    response = service(vals)
                else:
                    response = service(**vals)
                try:
                    root = ET.fromstring(response.text)
                    error_text = next(root.iter("faultstring")).text
                    error_message = next(root.iter("message")).text
                    error_code = next(root.iter("code")).text
                    raise ValidationError(
                        _(
                            "Error in the request to the Schenker API. This is the "
                            "thrown message:\n\n"
                            "[%s]\n"
                            "%s - %s" % (error_text, error_code, error_message)
                        )
                    )
                except ValidationError:
                    raise
                # If we can't get the proper exception, fallback to the first
                # exception error traceback
                except Exception:
                    raise Fault(e)
        return response

    # Booking API methods

    def _shipping_type_method(self, method):
        """Map shipping method with API method. Note that currently only land
        is supported. Default to land to ensure a method is provided.
        :params string with shipping method
        :returns string with the mapped key value for the proper method
        """
        method_map = {
            "land": "getBookingRequestLand",
            "air": "getBookingRequestAir",
            "ocean_fcl": "getBookingRequestOceanFCL",
            "ocean_lcl": "getBookingRequestOceanLCL",
        }
        return method_map.get("method", "getBookingRequestLand")

    def _shipping_api_credentials(self):
        """Each API has a different credentials SOAP declaration"""
        credentials = {"applicationArea": {"accessKey": self.access_key}}
        if self.user:
            credentials["applicationArea"]["userId"] = self.user
        if self.group_id:
            credentials["applicationArea"]["groupId"] = self.group_id
        return credentials

    def _scheneker_shipping_api_wrapper(self, method=False):
        """Aside from a different API method, each one has its own wrapper"""
        booking_wrapper_map = {
            "land": "bookingLand",
            "air": "bookingAir",
            "ocean_fcl": "bookingOceanFCL",
            "ocean_lcl": "bookingOceanLCL",
        }
        return booking_wrapper_map.get(method, "land")

    def _send_shipping(self, picking_vals, method=False):
        """Create new shipment
        :params vals dict of needed values
        :returns dict with Schenker response containing the shipping code and label
        """
        vals = self._shipping_api_credentials()
        method_wrapper = self._scheneker_shipping_api_wrapper(method)
        vals[method_wrapper] = picking_vals
        # From the Schenker docs:
        # Defines if booking shall be submitted. If false, the booking can be edited
        # in the frontend and MUST be submitted manually.
        vals[method_wrapper].update({"submitBooking": True})
        response = self._process_reply(
            self.client.service[self._shipping_type_method(method)], vals
        )
        return {"booking_id": response.bookingId, "barcode": response.barcodeDocument}

    def _shipping_label(self, reference_list=None, label_format="A6"):
        """Get shipping label for the given ref
        :param list reference -- shipping reference list
        :returns: base64 with pdf labels
        """
        reference_list = reference_list or []
        vals = dict(
            **self._shipping_api_credentials(),
            **{"barcodeRequest": {"format": label_format}}
        )
        vals["barcodeRequest"].update({"bookingId": ref for ref in reference_list})
        label = self._process_reply(
            self.client.service.getBookingBarcodeRequest, vals
        ).document
        return label

    def _cancel_shipment(self, reference=False):
        """Cancel de expedition for the given ref
        :param str reference -- booking reference string
        :returns: bool True if success
        """
        vals = self._shipping_api_credentials()
        vals.update({"cancelRequest": {"bookingId": reference}})
        response = self._process_reply(
            self.client.service.getBookingCancelRequest, vals
        )
        # TODO: Inspect typical response as we don't want to return a zeep  object.
        # Anyway, it's going to fail if the booking can't be cancelled. So either we
        # receive an exception error or the booking is cancelled.
        return bool(response)

    # Tracking API methods

    def _tracking_api_credentials(self):
        """Each API has a different credentials SOAP declaration"""
        return {"AccessKey": self.access_key, "in": {}}

    def _get_tracking_states(
        self, reference=False, reference_type="cu", booking_type="land"
    ):
        if not reference:
            return {}
        vals = self._tracking_api_credentials()
        vals["in"].update(
            {
                "referenceNumber": reference,
                "referenceType": reference_type,
                "transportNature": "exp" if booking_type == "land" else "int",
            }
        )
        response = self._process_reply(
            self.client.service.getPublicShipmentDetails, vals, send_as_kw=True
        )
        return {"shipment": response.Shipment}
