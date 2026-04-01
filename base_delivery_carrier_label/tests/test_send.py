# Copyright 2020 Hunki Enterprises BV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import base64
from unittest import mock

from odoo.tests.common import TransactionCase


class TestSend(TransactionCase):
    """Test sending a picking"""

    def test_send(self):
        """Test if the module picks up labels returned from
        delivery.carrier#send"""
        carrier = self.env.ref("delivery.delivery_carrier")
        picking_type = self.env.ref("stock.picking_type_out")
        # Note: Form() not used here due to a known issue with
        # carrier_id.integration_level expression evaluation in
        # stock_delivery views (evaluates on int instead of record).
        picking = self.env["stock.picking"].create(
            {
                "partner_id": self.env["res.partner"].create({"name": "Test"}).id,
                "picking_type_id": picking_type.id,
                "carrier_id": carrier.id,
                "location_id": (picking_type.default_location_src_id.id),
                "location_dest_id": (picking_type.default_location_dest_id.id),
            }
        )
        package = self.env["stock.quant.package"].create({})

        with mock.patch.object(type(carrier), "base_on_rule_send_shipping") as mocked:
            mocked.return_value = [
                dict(
                    labels=[
                        dict(
                            name="hello_world.pdf",
                            file=base64.b64encode(bytes("hello world", "utf8")),
                            file_type="pdf",
                            package_id=package.id,
                            tracking_number="Test package tracking ref",
                            parcel_tracking_uri="https://my_package_tracking_url",
                        ),
                    ]
                )
            ]
            labels_before = self.env["shipping.label"].search([])
            carrier.send_shipping(picking)
            label = self.env["shipping.label"].search([]) - labels_before
            self.assertTrue(label, "No label created")
            self.assertEqual(
                label.mimetype, "application/pdf", "Wrong attachment created"
            )
            self.assertEqual(package.parcel_tracking, "Test package tracking ref")
            self.assertEqual(
                package.parcel_tracking_uri, "https://my_package_tracking_url"
            )
