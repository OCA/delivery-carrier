# Copyright 2025 ACSONE SA/NV
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
import base64

from odoo.addons.base.tests.common import BaseCommon


class TestCarrierImage(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product = cls.env["product.product"].create(
            {"name": "Carrier", "type": "service"}
        )
        cls.carrier = cls.env["delivery.carrier"].create(
            {
                "name": "Test Carrier",
                "product_id": cls.product.id,
            }
        )

    def test_image(self):
        self.assertFalse(self.carrier.has_image)
        self.carrier.image_128 = base64.b64encode(b"<svg/>")
        self.assertTrue(self.carrier.has_image)
