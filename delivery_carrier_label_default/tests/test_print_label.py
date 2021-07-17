# Copyright 2021 Sunflower IT (http://sunflowerweb.nl)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import mock

from odoo.tests.common import Form, TransactionCase


class TestPrintLabel(TransactionCase):
    """Test print a default label """

    def test_print_label(self):
        """Test if the module picks up default labels returned from
        delivery.carrier#send"""
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
                {
                    "exact_price": carrier.fixed_price,
                    "tracking_number": False,
                }
            ]
            carrier.send_shipping(picking)
        attachment = self.env["ir.attachment"].search(
            [("name", "=ilike", ("%" + picking.name + "%"))]
        )
        self.assertEqual(
            attachment.mimetype, "application/pdf", "Wrong attachment created"
        )
        self.assertTrue(len(attachment) == 1)
