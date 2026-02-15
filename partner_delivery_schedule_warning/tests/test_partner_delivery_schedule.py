# Copyright 2026 NICO SOLUTIONS - Nils Coenen
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command

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
        self.assertIn(
            "09:00-11:00", warning, f"Expected warning for picking {self.picking.id}"
        )

    def test_write_triggers_on_partner_ids(self):
        new_partner = self.env["res.partner"].create({"name": "Another Partner"})
        self.schedule.write(
            {"partner_ids": [Command.set([self.partner.id, new_partner.id])]}
        )
        order = self.env["sale.order"].create(
            {
                "partner_id": new_partner.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "product_uom_qty": 1,
                            "price_unit": 10.0,
                        },
                    )
                ],
            }
        )
        order.action_confirm()
        pickings = self.env["stock.picking"].search(
            [("partner_id", "in", [new_partner.id])]
        )
        self.assertTrue(pickings, "Expected at least one picking for new_partner")
        for picking in pickings:
            warning = getattr(picking, "partner_delivery_schedule_warning", "")
            self.assertTrue(warning, f"Expected warning for picking {picking.id}")

    def test_create_triggers_pickings(self):
        new_schedule = self.env["delivery.schedule"].create(
            {
                "name": "test create",
                "hour_from": 12,
                "hour_to": 14,
                "monday": True,
                "partner_ids": [Command.set([self.partner.id])],
            }
        )
        pickings = self.env["stock.picking"].search(
            [("partner_id", "in", new_schedule.partner_ids.ids)]
        )
        for picking in pickings:
            warning = getattr(picking, "partner_delivery_schedule_warning", "")
            self.assertTrue(warning, f"Expected warning for picking {picking.id}")

    def test_create_with_partner_ids_as_ints(self):
        new_schedule = self.env["delivery.schedule"].create(
            {
                "name": "test int ids",
                "hour_from": 15,
                "hour_to": 16,
                "monday": True,
                "partner_ids": [self.partner.id],
            }
        )
        self.assertEqual(new_schedule.partner_ids.ids, [self.partner.id])
