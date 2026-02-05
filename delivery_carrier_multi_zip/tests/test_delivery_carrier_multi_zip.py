# Copyright 2022 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


from odoo.addons.base.tests.common import BaseCommon


class TestDeliveryCarrierMultiZip(BaseCommon):
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
                "zip_option": "range",
                "zip_range_ids": [(0, 0, {"zip_from": "0001", "zip_to": "0001"})],
            }
        )
        cls.order_1 = cls.env["sale.order"].create(
            {
                "partner_id": cls.partner_1.id,
            }
        )
        cls.order_2 = cls.env["sale.order"].create(
            {
                "partner_id": cls.partner_2.id,
            }
        )

    def test_available_carriers(self):
        self.assertIn(
            self.carrier, self.carrier.available_carriers(self.partner_1, self.order_1)
        )
        self.assertNotIn(
            self.carrier, self.carrier.available_carriers(self.partner_2, self.order_2)
        )
        self.carrier.zip_range_ids = [(0, 0, {"zip_from": "0002", "zip_to": "0020"})]
        self.assertIn(
            self.carrier, self.carrier.available_carriers(self.partner_2, self.order_2)
        )
