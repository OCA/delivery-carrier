# Copyright 2026 arielbarreiros96 (https://github.com/arielbarreiros96)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl)

from odoo import Command
from odoo.exceptions import UserError
from odoo.tests import HttpCase, tagged
from odoo.tools import mute_logger

from odoo.addons.http_routing.tests.common import MockRequest

from ..controllers.portal import SendcloudReturnPortal

RETURN_PORTAL_URL = "https://returnportal.sendcloud.sc/return/123456"


@tagged("post_install", "-at_install")
class TestPortalOnlineReturn(HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env["sendcloud.integration"].create(
            {
                "shop_name": "Test Shop",
                "public_key": "test-public-key",
                "secret_key": "test-secret-key",
                "company_id": cls.env.company.id,
            }
        )
        cls.shipping_product = cls.env["product.product"].create(
            {"name": "Shipping", "type": "service"}
        )
        cls.carrier = cls.env["delivery.carrier"].create(
            {
                "name": "Sendcloud Unstamped Letter",
                "delivery_type": "sendcloud",
                "sendcloud_code": 8,
                "company_id": cls.env.company.id,
                "product_id": cls.shipping_product.id,
            }
        )
        cls.paper_carrier = cls.env["delivery.carrier"].create(
            {
                "name": "Paper Carrier",
                "delivery_type": "fixed",
                "product_id": cls.shipping_product.id,
            }
        )
        cls.partner = cls.env["res.partner"].create({"name": "Portal Customer"})
        cls.product = cls.env["product.product"].create(
            {"name": "Returned Product", "is_storable": True}
        )

    def _create_delivery(self, carrier):
        picking_type = self.env.ref("stock.picking_type_out")
        picking = self.env["stock.picking"].create(
            {
                "partner_id": self.partner.id,
                "carrier_id": carrier.id,
                "picking_type_id": picking_type.id,
                "location_id": picking_type.default_location_src_id.id,
                "location_dest_id": self.env.ref("stock.stock_location_customers").id,
                "move_ids": [
                    Command.create(
                        {
                            "product_id": self.product.id,
                            "product_uom_qty": 1.0,
                            "product_uom": self.product.uom_id.id,
                        }
                    )
                ],
            }
        )
        picking.action_confirm()
        return picking

    def _create_parcel(self, picking, sendcloud_code=4242):
        return self.env["sendcloud.parcel"].create(
            {
                "name": "Outgoing Parcel",
                "sendcloud_code": sendcloud_code,
                "picking_id": picking.id,
                "company_id": self.env.company.id,
                "return_portal_url": RETURN_PORTAL_URL,
            }
        )

    def test_a_sendcloud_delivery_has_a_return_portal(self):
        picking = self._create_delivery(self.carrier)
        self._create_parcel(picking)
        self.assertEqual(picking._sendcloud_return_portal_url(), RETURN_PORTAL_URL)

    def test_a_delivery_without_a_parcel_has_no_return_portal(self):
        picking = self._create_delivery(self.carrier)
        self.assertEqual(picking._sendcloud_return_portal_url(), "")

    def test_another_carrier_has_no_return_portal(self):
        picking = self._create_delivery(self.paper_carrier)
        self._create_parcel(picking)
        self.assertEqual(picking._sendcloud_return_portal_url(), "")

    def _patch_return_portal_url(self, url):
        integration = self.env.company.sendcloud_default_integration_id

        def get_return_portal_url(self, code):
            return {"url": url}

        self.patch(type(integration), "get_return_portal_url", get_return_portal_url)

    def test_the_return_portal_url_is_fetched_when_missing(self):
        picking = self._create_delivery(self.carrier)
        parcel = self._create_parcel(picking)
        parcel.return_portal_url = False
        self._patch_return_portal_url(RETURN_PORTAL_URL)
        self.assertEqual(picking._sendcloud_return_portal_url(), RETURN_PORTAL_URL)

    def test_a_parcel_sendcloud_gives_no_portal_for_keeps_the_slip(self):
        picking = self._create_delivery(self.carrier)
        parcel = self._create_parcel(picking)
        parcel.return_portal_url = False
        self._patch_return_portal_url(None)
        self.assertEqual(picking._sendcloud_return_portal_url(), "")

    @mute_logger(
        "odoo.addons.delivery_sendcloud_oca_return_portal.models.stock_picking"
    )
    def test_a_failing_return_portal_lookup_keeps_the_slip(self):
        picking = self._create_delivery(self.carrier)
        parcel = self._create_parcel(picking)
        parcel.return_portal_url = False
        integration = self.env.company.sendcloud_default_integration_id

        def get_return_portal_url(self, code):
            raise UserError(self.env._("Sendcloud: server not reachable"))

        self.patch(type(integration), "get_return_portal_url", get_return_portal_url)
        self.assertEqual(picking._sendcloud_return_portal_url(), "")

    def test_deleting_a_shipment_sendcloud_never_saw_is_tolerated(self):
        integration = self.env.company.sendcloud_default_integration_id

        def delete_shipments(self, integration_code, vals):
            return {"error": {"code": 404, "message": "Not found"}}

        self.patch(type(integration), "delete_shipments", delete_shipments)
        self.env["stock.picking"].delete_sendcloud_pickings(
            {integration.id: [{"external_shipment_id": "42"}]}
        )

    def test_sendcloud_refusing_a_deletion_stops_the_cancellation(self):
        integration = self.env.company.sendcloud_default_integration_id

        def delete_shipments(self, integration_code, vals):
            return {"error": {"code": 410, "message": "Parcel is already in transit"}}

        self.patch(type(integration), "delete_shipments", delete_shipments)
        with self.assertRaises(UserError) as caught:
            self.env["stock.picking"].delete_sendcloud_pickings(
                {integration.id: [{"shipment_uuid": "abc"}]}
            )
        self.assertIn("already in transit", str(caught.exception))

    def test_sale_order_return_is_sent_to_the_sendcloud_portal(self):
        picking = self._create_delivery(self.carrier)
        self._create_parcel(picking)
        self.authenticate("admin", "admin")
        response = self.url_open(
            f"/my/picking/return/pdf/{picking.id}", allow_redirects=False
        )
        self.assertIn(response.status_code, (302, 303))
        self.assertEqual(response.headers["Location"], RETURN_PORTAL_URL)

    def test_sale_order_return_without_portal_keeps_the_slip(self):
        picking = self._create_delivery(self.carrier)
        self.authenticate("admin", "admin")
        response = self.url_open(
            f"/my/picking/return/pdf/{picking.id}", allow_redirects=False
        )
        self.assertEqual(response.status_code, 200)

    def test_any_portal_return_slip_is_sent_to_the_sendcloud_portal(self):
        picking = self._create_delivery(self.carrier)
        self._create_parcel(picking)
        with MockRequest(self.env) as request:
            request.redirect = lambda location, **kwargs: location
            response = SendcloudReturnPortal()._show_report(
                picking, "pdf", "stock.return_label_report"
            )
        self.assertEqual(response, RETURN_PORTAL_URL)
