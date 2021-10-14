# Copyright 2021 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from .common import DeliveryLocalPickupCommon


class DeliveryLocalPickup(DeliveryLocalPickupCommon):
    def setUp(self):
        super().setUp()

    def test_order_delivery_carrier_rate_shipment(self):
        res = self.carrier.local_pickup_rate_shipment(self.sale)
        self.assertEqual(res["price"], 0)
        self.assertTrue(res["success"])

    def test_delivery_carrier_local_pickup(self):
        self.picking.action_confirm()
        self.picking.action_assign()
        self.picking.send_to_shipper()
        self.assertTrue(self.picking.carrier_tracking_ref)
        self.assertTrue(
            "/local_pickup/%s" % self.picking.id in self.picking.carrier_tracking_url
        )
