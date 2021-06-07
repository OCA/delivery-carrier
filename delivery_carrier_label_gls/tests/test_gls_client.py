# coding: utf-8
# Copyright 2021 ACSONE SA/NV.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import unittest

from odoo.exceptions import ValidationError

from .common import TestGLS


# to run these tests, you need to put your GLS credentials into the carrier
# in the common setup.
@unittest.skip("gls_client")
class TestGlsClient(TestGLS):
    @property
    def create_payload(self):
        return {
            "Shipment": {
                "Consignee": {
                    "Address": {
                        "Name1": "DALEMANS, Bert Courtyn",
                        "Street": "42, MEERSBLOEM MELDEN",
                        "CountryCode": "BE",
                        "ZIPCode": "9700",
                        "City": "OUDENAARDE",
                        "ContactPerson": "John",
                        "eMail": "bart.bart@xyz.be",
                        "FixedLinePhonenumber": "0495",
                    }
                },
                "ShipmentUnit": [{"Weight": 5}],
                "Product": "PARCEL",
            },
        }

    def test_bad_request_allowed_services(self):
        bad_payload = {
            "Source": {
                "CountryCode": "LX",  # nonexistent countryCode!
                "ZIPCode": "9800",
            },
            "Destination": {"CountryCode": "BE", "ZIPCode": "1620"},
        }
        with self.assertRaises(ValidationError):
            self.gls_client.getAllowedServices(bad_payload)

    def test_get_allowed_services(self):
        payload = {
            "Source": {"CountryCode": "BE", "ZIPCode": "1367"},
            "Destination": {"CountryCode": "BE", "ZIPCode": "1620"},
        }
        response = self.gls_client.getAllowedServices(payload)

        self.assertTrue({"ProductName": "PARCEL"} in response["AllowedServices"])
        # sample_response = {'AllowedServices': [{'ProductName': 'PARCEL'},
        #                      {'ProductName': 'EXPRESS'},
        #                      {'ServiceName': 'service_Saturday'},
        #                      {'ServiceName': 'service_pickandship'},
        #                      {'ServiceName': 'service_shopdelivery'},
        #                      {'ServiceName': 'service_0900'},
        #                      {'ServiceName': 'service_saturday_1200'},
        #                      {'ServiceName': 'service_easystart'},
        #                      {'ServiceName': 'service_cash'},
        #                      {'ServiceName': 'service_flexdelivery'},
        #                      {'ServiceName': 'service_pickandreturn'},
        #                      {'ServiceName': 'service_1200'},
        #                      {'ServiceName': 'service_shopreturn'},
        #                      {'ServiceName': 'service_1000'}]}

    def test_flow(self):
        # firstly we create then cancel a package
        response_create_cancel = self.gls_client.create_parcel(self.create_payload)
        parcel_data = response_create_cancel["CreatedShipment"]["ParcelData"][0]
        tracking_cancel = parcel_data["TrackID"]
        self.assertEqual(
            len(response_create_cancel["CreatedShipment"]["ParcelData"]), 1
        )
        self.assertTrue(len(tracking_cancel))
        self.assertTrue("PrintData" in response_create_cancel["CreatedShipment"])
        response_cancel = self.gls_client.cancel_parcel(tracking_cancel)
        self.assertEqual(response_cancel["TrackID"], tracking_cancel)
        cancellation_result = ["CANCELLED", "CANCELLATION_PENDING"]
        self.assertTrue(response_cancel["result"] in cancellation_result)

        # secondly we create a package then get a report
        response_create = self.gls_client.create_parcel(self.create_payload)
        tracking = response_create["CreatedShipment"]["ParcelData"][0]["TrackID"]
        report = self.gls_client.get_end_of_day_report()
        # WARNING if you called create_parcel before, [0] won't work
        self.assertEqual(len(report["Shipments"]), 1)
        # the parcel that we canceled does not appear in the report
        tracking_response = report["Shipments"][0]["ShipmentUnit"][0]["TrackID"]
        self.assertEqual(tracking_response, tracking)
        # the next call does not return parcels for which we already have a report
        empty_report = self.gls_client.get_end_of_day_report()
        self.assertEqual(empty_report, {})

        # cannot cancel once the report is done
        with self.assertRaises(ValidationError):
            self.gls_client.cancel_parcel(tracking)

    def test_create_wrong_shipment(self):
        """Check that with a wrong parameter, we get an exception."""
        bad_payload = self.create_payload
        bad_payload["Shipment"]["Consignee"]["CountryCode"] = "LX"

        with self.assertRaises(ValidationError):
            self.gls_client.validate_parcel(bad_payload)
        with self.assertRaises(ValidationError):
            self.gls_client.create_parcel(bad_payload)

    def test_wrong_cancel(self):
        parcel_tracking = "doesnotexist"
        with self.assertRaises(ValidationError):
            self.gls_client.cancel_parcel(parcel_tracking)

    def test_get_parcel_shops(self):
        belgium = self.env.ref("base.be")
        response = self.gls_client.getParcelShopsByCountryCode(belgium.code)
        self.assertTrue(len([p["ParcelShopID"] for p in response["ParcelShop"]]))
