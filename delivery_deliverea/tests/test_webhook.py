# © 2023 - FactorLibre - Oscar Indias <oscar.indias@factorlibre.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests import common

from ..controllers.main import DelivereaWebhook
from .tools import MockRequest


class TestWebhook(common.TransactionCase):
    def setUp(self):
        super().setUp()
        self.full_url = "/deliverea-tracking-webhook"
        self.headers = {
            "Content-Type": "application/json",
            "environ": {
                "REQUEST_METHOD": "POST",
            },
        }
        self.shipping_product = self.env.ref("delivery.product_product_local_delivery")
        distribution_center = self.env["deliverea.distribution.center"].create(
            {
                "name": "Default Distribution Center",
                "uuid": "123",
            }
        )
        self.params = [
            {
                "delivereaReference": "Sbe2fd53e94869d",
                "trackingCode": "01",
                "advancedTrackingUrl": "Test Tracking Url",
                "trackingDetails": "Test Tracking Details",
            }
        ]
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
                "deliverea_reference": "Sbe2fd53e94869d",
            }
        )

    def test_01(self):
        self.assertFalse(self.picking.delivery_state)
        request = MockRequest(
            self.env, headers=self.headers, data=self.params, path=self.full_url
        )
        req = MockRequest(self.env)
        req.request = request.request
        with req:
            DelivereaWebhook.order_import_webhook(DelivereaWebhook)
        self.assertTrue(self.picking.delivery_state)
