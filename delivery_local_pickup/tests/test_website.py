# Copyright 2021 Tecnativa - Víctor Martínez
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl)
import odoo.tests

from .common import DeliveryLocalPickupCommon


class TesDeliveryLOcalPickupWebsite(DeliveryLocalPickupCommon, odoo.tests.HttpCase):
    def setUp(self):
        super().setUp()

    def test_local_pickup_tour(self):
        self.picking.action_confirm()
        self.picking.action_assign()
        self.picking.send_to_shipper()
        self.start_tour(
            "/local_pickup/%s" % self.picking.id, "delivery_local_pickup_tour"
        )
