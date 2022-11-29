# Copyright 2020 Hunki Enterprises BV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import base64

from odoo.tests.common import TransactionCase


class TestHelperFunctions(TransactionCase):
    """Test convenience functions on stock.picking"""

    def test_attach_shipping_label(self):
        """Test if attaching labels works correctly"""
        picking = self.env["stock.picking"].new(
            dict(
                carrier_id=self.env.ref("delivery.delivery_carrier").id,
                company_id=self.env.user.company_id.id,
            )
        )
        label = picking.with_context(
            # test if the function protect against an unwanted key in the context
            default_type="binary",
        ).attach_shipping_label(
            dict(
                name="hello_world.pdf",
                file=base64.b64encode(bytes("hello world", "utf8")),
                file_type="pdf",
                package_id=self.env["stock.quant.package"]
                .create(dict(name="package"))
                .id,
                tracking_number="hello",
            )
        )
        self.assertEqual(label.name, "hello_world.pdf")

    def test_delivery_carrier_option(self):
        """Mandatory option on delivery options sets color"""
        option = self.env["delivery.carrier.option"].create(
            {
                "name": __name__,
                "code": __name__,
            }
        )
        self.assertFalse(option.color)
        option.mandatory = True
        self.assertEqual(option.color, 2)
