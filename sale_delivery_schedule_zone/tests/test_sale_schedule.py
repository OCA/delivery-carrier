# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import datetime

from freezegun import freeze_time

from odoo.tests import tagged

from odoo.addons.partner_delivery_schedule_zone.tests.common import (
    DeliveryZoneScheduleCommon,
)


@tagged("post_install", "-at_install")
class TestSaleDeliverySchedule(DeliveryZoneScheduleCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # 5-minute cutoff, deterministic per company.
        cls.env.company.delivery_cutoff_minutes = 5
        cls.product = cls.env["product.product"].create(
            {
                "name": "Storable Product",
                "type": "consu",
                "is_storable": True,
            }
        )

    def _create_order(self, partner=None):
        return self.env["sale.order"].create(
            {
                "partner_id": (partner or self.partner_a).id,
                "order_line": [
                    (0, 0, {"product_id": self.product.id, "product_uom_qty": 5.0})
                ],
            }
        )

    @freeze_time("2026-06-09 07:00:00")
    def test_assigns_next_reachable_slot(self):
        order = self._create_order()
        self.assertFalse(order.delivery_schedule_id)
        order.action_confirm()
        self.assertEqual(order.delivery_schedule_id, self.schedule_8h)
        self.assertEqual(order.scheduled_date, datetime(2026, 6, 9, 8, 0, 0))

    @freeze_time("2026-06-09 07:00:00")
    def test_cutoff_time_is_five_minutes_before(self):
        order = self._create_order()
        order.action_confirm()
        delta = order.scheduled_date - order.cutoff_time
        self.assertEqual(delta.total_seconds(), 300)

    @freeze_time("2026-06-09 07:57:00")
    def test_within_cutoff_rolls_to_following_slot(self):
        # 08:00 is only 3 min away (< 5 min cutoff) so it is skipped.
        order = self._create_order()
        order.action_confirm()
        self.assertEqual(order.delivery_schedule_id, self.schedule_14h)
        self.assertEqual(order.scheduled_date, datetime(2026, 6, 9, 14, 0, 0))

    @freeze_time("2026-06-09 15:00:00")
    def test_after_last_departure_rolls_to_next_day(self):
        order = self._create_order()
        order.action_confirm()
        self.assertEqual(order.delivery_schedule_id, self.schedule_8h)
        self.assertEqual(order.scheduled_date, datetime(2026, 6, 10, 8, 0, 0))

    @freeze_time("2026-06-09 07:00:00")
    def test_no_zone_no_assignment(self):
        order = self._create_order(partner=self.partner_no_zone)
        order.action_confirm()
        self.assertFalse(order.delivery_schedule_id)
        self.assertFalse(order.scheduled_date)

    @freeze_time("2026-06-09 07:00:00")
    def test_already_assigned_slot_is_kept(self):
        order = self._create_order()
        order.delivery_schedule_id = self.schedule_14h
        order.scheduled_date = datetime(2026, 6, 9, 14, 0, 0)
        order.action_confirm()
        self.assertEqual(order.delivery_schedule_id, self.schedule_14h)

    @freeze_time("2026-06-09 07:00:00")
    def test_cutoff_minutes_from_company(self):
        self.env.company.delivery_cutoff_minutes = 30
        order = self._create_order()
        order.action_confirm()
        delta = order.scheduled_date - order.cutoff_time
        self.assertEqual(delta.total_seconds(), 1800)
