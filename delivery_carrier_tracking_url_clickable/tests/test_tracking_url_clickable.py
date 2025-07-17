# Copyright - 2025 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestTrackingURLClickable(TransactionCase):
    def setUp(self):
        super().setUp()

        self.carrier_product = self.env["product.product"].create(
            {
                "name": "Test Shipping Product",
                "type": "service",
            }
        )

        self.carrier = self.env["delivery.carrier"].create(
            {
                "name": "Test Carrier",
                "delivery_type": "fixed",
                "product_id": self.carrier_product.id,
                "fixed_price": 5.0,
                "default_tracking_url": "https://track.example.com/",
                "tracking_number_separator": ",",
            }
        )

        self.picking = self.env["stock.picking"].create(
            {
                "carrier_id": self.carrier.id,
                "picking_type_id": self.env.ref("stock.picking_type_out").id,
                "location_id": self.env.ref("stock.stock_location_stock").id,
                "location_dest_id": self.env.ref("stock.stock_location_customers").id,
                "move_ids_without_package": [],
            }
        )

    def test_tracking_url_clickable_single_ref(self):
        self.picking.carrier_tracking_ref = "ABC123"
        self.picking._compute_tracking_url_clickable()
        expected_html = (
            '<a href="https://track.example.com/ABC123" target="_blank">ABC123</a>'
        )
        self.assertEqual(self.picking.tracking_url_clickable, expected_html)

    def test_tracking_url_clickable_multiple_refs(self):
        self.picking.carrier_tracking_ref = "ABC123, XYZ789"
        self.picking._compute_tracking_url_clickable()
        html = self.picking.tracking_url_clickable
        self.assertIn('href="https://track.example.com/ABC123"', html)
        self.assertIn(">ABC123<", html)
        self.assertIn('href="https://track.example.com/XYZ789"', html)
        self.assertIn(">XYZ789<", html)

    def test_tracking_url_clickable_no_tracking_ref(self):
        self.picking._compute_tracking_url_clickable()
        self.assertFalse(self.picking.tracking_url_clickable)
