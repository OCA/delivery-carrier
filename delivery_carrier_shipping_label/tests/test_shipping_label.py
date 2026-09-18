# Copyright 2020 Hunki Enterprises BV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import base64

from odoo.exceptions import UserError

from odoo.addons.delivery.tests.common import DeliveryCommon


class TestShippingLabel(DeliveryCommon):
    def test_attach_shipping_label(self):
        """Test if attaching labels works correctly"""
        wh = self.env["stock.warehouse"].search(
            [("company_id", "=", self.env.company.id)], limit=1
        )
        picking = self.env["stock.picking"].create(
            {
                "picking_type_id": wh.in_type_id.id,
                "location_id": self.ref("stock.stock_location_customers"),
                "location_dest_id": wh.lot_stock_id.id,
            }
        )
        label = picking.with_context(
            # test if the function protect against an unwanted key in the context
            default_type="binary",
        ).attach_shipping_label(
            dict(
                name="hello_world.pdf",
                file=base64.b64encode(bytes("hello world", "utf8")),
                file_type="pdf",
                package_id=self.env["stock.package"].create(dict(name="package")).id,
            )
        )
        self.assertEqual(label.name, "hello_world.pdf")
        with self.assertRaises(UserError):
            picking._check_existing_shipping_label()
