#  Copyright (c) 2026 Groupe Voltaire
#  @author Emilie SOUTIRAS  <emilie.soutiras@groupevoltaire.com>
#  License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import json
from unittest import mock

from odoo.tests.common import TransactionCase

from ..roulier_fedex import transport

TRANSPORT_REQUESTS = (
    "odoo.addons.delivery_roulier_fedex.roulier_fedex.transport.requests"
)


def _response(status_code, content):
    response = mock.Mock()
    response.status_code = status_code
    response.reason = "OK" if status_code == 200 else "Error"
    response.json.return_value = content
    response.elapsed.total_seconds.return_value = 0.1
    return response


class TestDeliveryRoulierFedex(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.company = cls.env.company
        cls.company.partner_id.write(
            {
                "street": "1 rue de la Paix",
                "zip": "75002",
                "city": "Paris",
                "country_id": cls.env.ref("base.fr").id,
                "phone": "0102030405",
            }
        )
        cls.account = cls.env["carrier.account"].create(
            {
                "name": "FedEx sandbox",
                "delivery_type": "fedex_rest",
                "account": "api-key",
                "password": "secret-key",
                "fedex_rest_account_number": "123456789",
                "company_id": cls.company.id,
            }
        )
        cls.carrier = cls.env.ref(
            "delivery_roulier_fedex.delivery_carrier_fedex_international_priority"
        )
        cls.carrier.write({"carrier_account_id": cls.account.id})
        us = cls.env.ref("base.us")
        new_york = cls.env["res.country.state"].search(
            [("country_id", "=", us.id), ("code", "=", "NY")]
        )
        cls.partner = cls.env["res.partner"].create(
            {
                "name": "John Doe",
                "street": "367 7th Ave",
                "zip": "10001",
                "city": "New York",
                "state_id": new_york.id,
                "country_id": us.id,
                "phone": "+1 877 339 2774",
            }
        )
        cls.product = cls.env["product.product"].create(
            {"name": "Saddle", "type": "product", "weight": 7.5, "lst_price": 2000}
        )
        cls.stock_location = cls.env.ref("stock.stock_location_stock")
        cls.env["stock.quant"]._update_available_quantity(
            cls.product, cls.stock_location, 1
        )

    def setUp(self):
        super().setUp()
        transport._token_cache.clear()

    def _create_picking(self):
        picking = self.env["stock.picking"].create(
            {
                "picking_type_id": self.env.ref("stock.picking_type_out").id,
                "location_id": self.stock_location.id,
                "location_dest_id": self.env.ref("stock.stock_location_customers").id,
                "partner_id": self.partner.id,
                "carrier_id": self.carrier.id,
                "move_ids": [
                    (
                        0,
                        0,
                        {
                            "name": self.product.name,
                            "product_id": self.product.id,
                            "product_uom_qty": 1,
                            "product_uom": self.product.uom_id.id,
                            "location_id": self.stock_location.id,
                            "location_dest_id": self.env.ref(
                                "stock.stock_location_customers"
                            ).id,
                        },
                    )
                ],
            }
        )
        picking.action_confirm()
        picking.action_assign()
        picking.move_line_ids.qty_done = 1
        # action_put_in_pack() would return the package type wizard
        # because the picking has a carrier
        picking._put_in_pack(picking.move_line_ids)
        return picking

    def _ship_response(self):
        return {
            "transactionId": "abc",
            "output": {
                "transactionShipments": [
                    {
                        "masterTrackingNumber": "794615064919",
                        "pieceResponses": [
                            {
                                "trackingNumber": "794615064919",
                                "packageDocuments": [
                                    {
                                        "contentType": "LABEL",
                                        "docType": "PDF",
                                        "encodedLabel": "JVBERi0xLjQK",
                                    }
                                ],
                            }
                        ],
                        "shipmentDocuments": [],
                    }
                ]
            },
        }

    def test_generate_label(self):
        picking = self._create_picking()
        with mock.patch(TRANSPORT_REQUESTS) as requests_mock:
            requests_mock.post.return_value = _response(
                200, {"access_token": "token", "expires_in": 3599}
            )
            requests_mock.request.return_value = _response(200, self._ship_response())
            picking.send_to_shipper()
        method, url = requests_mock.request.call_args.args
        self.assertEqual(method, "post")
        self.assertEqual(url, "https://apis-sandbox.fedex.com/ship/v1/shipments")
        body = json.loads(requests_mock.request.call_args.kwargs["data"])
        shipment = body["requestedShipment"]
        self.assertEqual(shipment["serviceType"], "FEDEX_INTERNATIONAL_PRIORITY")
        self.assertEqual(
            shipment["recipients"][0]["address"]["stateOrProvinceCode"], "NY"
        )
        self.assertEqual(
            shipment["requestedPackageLineItems"][0]["weight"]["value"], 7.5
        )
        self.assertEqual(
            len(shipment["customsClearanceDetail"]["commodities"]),
            1,
            "US needs customs",
        )
        self.assertEqual(picking.carrier_tracking_ref, "794615064919")
        self.assertEqual(picking.package_ids.parcel_tracking, "794615064919")

    def test_token_is_cached(self):
        picking = self._create_picking()
        with mock.patch(TRANSPORT_REQUESTS) as requests_mock:
            requests_mock.post.return_value = _response(
                200, {"access_token": "token", "expires_in": 3599}
            )
            requests_mock.request.return_value = _response(200, self._ship_response())
            picking.send_to_shipper()
            picking.package_ids.parcel_tracking = False
            picking.carrier_tracking_ref = False
            picking.carrier_id.send_shipping(picking)
        self.assertEqual(requests_mock.post.call_count, 1)

    def test_cancel_shipment(self):
        picking = self._create_picking()
        picking.carrier_tracking_ref = "794615064919"
        with mock.patch(TRANSPORT_REQUESTS) as requests_mock:
            requests_mock.post.return_value = _response(
                200, {"access_token": "token", "expires_in": 3599}
            )
            requests_mock.request.return_value = _response(
                200, {"output": {"cancelledShipment": True}}
            )
            picking.cancel_shipment()
        method, url = requests_mock.request.call_args.args
        self.assertEqual(method, "put")
        self.assertTrue(url.endswith("/ship/v1/shipments/cancel"))
        self.assertFalse(picking.carrier_tracking_ref)
