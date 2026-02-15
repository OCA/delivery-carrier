# Copyright 2026 NICO SOLUTIONS - Nils Coenen
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.addons.base.tests.common import BaseCommon


class TestPartnerDeliverySchedule(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.schedule = cls.env["delivery.schedule"].create(
            {
                "name": "test",
                "hour_from": 8,
                "hour_to": 10,
                "monday": True,
                "tuesday": True,
                "wednesday": False,
                "thursday": False,
                "friday": False,
            }
        )
        cls.partner = cls.env["res.partner"].create(
            {
                "name": "test",
                "delivery_schedule_ids": [(6, 0, cls.schedule.ids)],
            }
        )
        cls.product = cls.env["product.product"].create(
            {"name": "Test product", "type": "consu", "is_storable": True}
        )
        cls.order = (
            cls.env["sale.order"]
            .with_context(default_sale_order_template_id=False)
            .create(
                {
                    "partner_id": cls.partner.id,
                    "order_line": [
                        (
                            0,
                            0,
                            {
                                "product_id": cls.product.id,
                                "product_uom_qty": 1,
                                "price_unit": 10.0,
                            },
                        )
                    ],
                }
            )
        )
        cls.order.action_confirm()
        cls.picking = cls.order.picking_ids[0]

    def test_write_triggers_pickings(self):
        self.schedule.write({"hour_from": 9, "hour_to": 11})
        self.picking = self.env["stock.picking"].browse(self.picking.id)
        warning = getattr(self.picking, "partner_delivery_schedule_warning", "")
        self.assertIn("09:00-11:00", warning)
