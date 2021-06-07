# coding: utf-8
# Copyright 2021 ACSONE SA/NV.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests.common import SavepointCase


class TestGLS(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super(TestGLS, cls).setUpClass()

        cls.company = cls.env.user.company_id
        vals_gls_carrier = {
            "name": "Test GLS",
            "company_id": cls.company.id,
            "delivery_type": "gls",
            "gls_test": True,
            "gls_login": "LOGIN",  # Fill these if you want to test your integration
            "gls_password": "PASSWORD",  # the 3 parameters are needed by the client
            "gls_contact_id": "CONTACTID",  # you may need to adapt the test addresses
            "gls_url_test": "https://shipit-wbm-test01.gls-group.eu:8443/backend/rs/",
        }
        cls.gls_carrier = cls.env["delivery.carrier"].create(vals_gls_carrier)
        cls.gls_client = cls.env["delivery.client.gls"].create(
            {"carrier_id": cls.gls_carrier.id}
        )
        vals_product = {"name": "product", "type": "product", "weight": 0.5}
        cls.product = cls.env["product.product"].create(vals_product)
        vals_partner = {
            "name": "partner",
            "city": "Ramillies",
            "zip": "1367",
            "email": "rd@odoo.con",
            "street": "9, rue des bourlottes",
            "country_id": cls.env.ref("base.be").id,
        }
        cls.partner = cls.env["res.partner"].create(vals_partner)
        cls.gls_parcel_shop = "0560005537"
        vals_sale_order = {
            "partner_id": cls.partner.id,
            "gls_parcel_shop": cls.gls_parcel_shop,
            "carrier_id": cls.gls_carrier.id,
        }
        cls.sale_order = cls.env["sale.order"].create(vals_sale_order)
        vals_order_line = {
            "name": "Line Description",
            "order_id": cls.sale_order.id,
            "product_id": cls.product.id,
        }
        cls.order_line = cls.env["sale.order.line"].create(vals_order_line)


class MockGlsClient(object):
    def __init__(self):
        self.report_counter = 0

    def cancel_parcel(self, parcel_tracking):
        return {"TrackID": parcel_tracking, "result": "CANCELLATION_PENDING"}

    def create_parcel(self, shipment_payload):
        return {
            u"CreatedShipment": {
                u"CustomerID": u"0560002709",
                u"GDPR": [
                    u"Information about Data Protection in GLS Group can be found at",
                    u"gls-group.eu/dataprotection",
                ],
                u"ParcelData": [
                    {
                        u"Barcodes": {
                            u"Primary1D": u"716649153647",
                            u"Primary1DPrint": True,
                            u"Primary2D": u"ABE7100BE7311...",
                            u"Secondary2D": u"A|Dagbladen...",
                        },
                        u"HandlingInformation": u"SHD S",
                        u"ParcelNumber": u"716649153647",
                        u"RoutingInfo": {
                            u"FinalLocationCode": u"BE7311",
                            u"HubLocation": u"B73",
                            u"InboundSortingFlag": u"2",
                            u"LastRoutingDate": u"2021-06-12",
                            u"Tour": u"1101",
                        },
                        u"ServiceArea": {
                            u"Service": [
                                {
                                    u"Header": u"ShopDeliveryService",
                                    u"Information": [
                                        {
                                            u"Name": u"ConsigneeName",
                                            u"Value": u"partner",
                                        },
                                        {u"Name": u"Phone", u"Value": u""},
                                    ],
                                }
                            ]
                        },
                        u"TrackID": u"ZMZE0SRO",
                    }
                ],
                u"PickupLocation": u"BE7100",
                u"PrintData": [{u"Data": u"JVeryLongString==", u"LabelFormat": u"PDF"}],
                u"ShipmentReference": [u"WH/OUT/00032"],
            }
        }

    def get_end_of_day_report(self, date=False):
        self.report_counter += 1
        result_payload = {
            "Shipments": [
                {
                    "Consignee": {
                        "Address": {
                            "City": "Ramillies",
                            "CountryCode": "BE",
                            "Name1": "partner",
                            "Street": "9, rue des bourlottes",
                            "ZIPCode": "1367",
                            "eMail": "rd@odoo.con",
                        }
                    },
                    "Product": "PARCEL",
                    "Service": [{"Service": {"ServiceName": "service_shopdelivery"}}],
                    "ShipmentUnit": [
                        {
                            "ParcelNumber": "716649153647",
                            "TrackID": "ZMZE0SRO",
                            "Weight": "0.5",
                        }
                    ],
                    "Shipper": {
                        "AlternativeShipperAddress": {
                            "City": "Drogenbos",
                            "CountryCode": "BE",
                            "FixedLinePhonenumber": "0032022222222",
                            "MobilePhoneNumber": "0032022222222",
                            "Name1": "Adress",
                            "Name2": "Depot 71",
                            "Street": "StreetName",
                            "StreetNumber": "42",
                            "ZIPCode": "4280",
                            "eMail": "email@example.com",
                        },
                        "ContactID": "CONTACTID",
                    },
                    "ShippingDate": "2021-06-14",
                }
            ]
        }
        return {} if self.report_counter > 1 else result_payload
