# Copyright 2022 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests import common

from odoo.addons.delivery_carrier_multi_zip.hooks import post_init_hook


class TestDeliveryCarrierMultiZip(common.SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner_1 = cls.env["res.partner"].create(
            {"name": "Test partner 1", "zip": "0001"}
        )
        cls.partner_2 = cls.env["res.partner"].create(
            {"name": "Test partner 2", "zip": "0002"}
        )
        cls.product = cls.env["product.product"].create(
            {"name": "Test carrier", "type": "service"}
        )
        cls.carrier = cls.env["delivery.carrier"].create(
            {
                "name": "Test carrier multi ZIP",
                "product_id": cls.product.id,
                "zip_from": "0001",
                "zip_to": "0001",
            }
        )

    def test_delivery_multi_zip_write_create(self):
        self.assertEqual(len(self.carrier.zip_ids), 1)
        self.assertEqual(self.carrier.zip_ids.zip_from, "0001")
        self.assertEqual(self.carrier.zip_ids.zip_to, "0001")
        self.carrier.write({"zip_to": "0002"})
        self.assertEqual(len(self.carrier.zip_ids), 2)
        self.assertEqual(self.carrier.zip_ids[1].zip_from, "0")
        self.assertEqual(self.carrier.zip_ids[1].zip_to, "0002")

    def test_post_init_hook(self):
        self.carrier.zip_ids.unlink()
        self.carrier.with_context(bypass_multi_zip=True).write({"zip_from": "0002"})
        post_init_hook(self.env.cr, None)
        self.assertEqual(len(self.carrier.zip_ids), 1)
        self.assertEqual(self.carrier.zip_ids.zip_from, "0002")
        self.assertEqual(self.carrier.zip_ids.zip_to, "z")
        self.carrier.refresh()
        self.assertFalse(self.carrier.zip_from)

    def test_available_carriers(self):
        self.assertIn(self.carrier, self.carrier.available_carriers(self.partner_1))
        self.assertNotIn(self.carrier, self.carrier.available_carriers(self.partner_2))
        self.carrier.zip_ids = [(0, 0, {"zip_from": "0002", "zip_to": "0020"})]
        self.assertIn(self.carrier, self.carrier.available_carriers(self.partner_2))
