# Copyright 2025 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo.addons.base.tests.common import BaseCommon


class TestDeliveryCarrierShippingPolicy(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.fee = cls.env["product.product"].create({"name": "FEE", "type": "service"})
        cls.carrier = cls.env["delivery.carrier"].create(
            {
                "name": "TEST",
                "product_id": cls.fee.id,
                "picking_policy": "one",
            }
        )
        cls.partner = cls.env["res.partner"].create({"name": "TEST"})
        cls.product = cls.env["product.product"].create(
            {"name": "TEST", "is_storable": True}
        )
        cls.order = cls.env["sale.order"].create(
            {
                "partner_id": cls.partner.id,
                "order_line": [(0, 0, {"product_id": cls.product.id})],
            }
        )

    def test_carrier_picking_policy(self):
        self.assertEqual(self.order.picking_policy, "direct")
        self.order.set_delivery_line(self.carrier, 100)
        self.assertEqual(self.order.picking_policy, "one")
        self.order.action_confirm()
