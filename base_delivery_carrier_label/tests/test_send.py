# Copyright 2020 Hunki Enterprises BV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import base64

import mock

from odoo.tests.common import Form, TransactionCase


class TestSend(TransactionCase):
    """Test sending a picking"""

    def test_send(self):
        """Test if the module picks up labels returned from delivery.carrier#send"""
        carrier = self.env.ref("delivery.normal_delivery_carrier")
        picking_form = Form(
            self.env["stock.picking"].with_context(
                default_picking_type_id=self.env.ref("stock.picking_type_out").id,
            )
        )
        picking_form.carrier_id = carrier
        picking = picking_form.save()

        with mock.patch.object(type(carrier), "fixed_send_shipping") as mocked:
            mocked.return_value = [
                dict(
                    labels=[
                        dict(
                            name="hello_world.pdf",
                            file=base64.b64encode(bytes("hello world", "utf8")),
                            file_type="pdf",
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
