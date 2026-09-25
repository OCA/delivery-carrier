# Copyright 2026 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from freezegun import freeze_time

from odoo.tests import tagged

from .common import DeliveryScheduleCommon

# Reference date: Wednesday 2026-06-17, 07:00 UTC
# - schedule_8h  opens at 08:00 Mon-Fri  → reachable today at 08:00 UTC
# - schedule_14h opens at 14:00 Mon-Fri  → reachable today at 14:00 UTC
# - schedule_sat opens at 09:00 Sat only → next occurrence: 2026-06-20


@tagged("post_install", "-at_install")
class TestGetNextSchedule(DeliveryScheduleCommon):
    @freeze_time("2026-06-17 07:00:00")
    def test_earliest_slot_is_returned(self):
        """Before 08:00, the 08:00 slot wins over 14:00."""
        schedule, departure = (self.schedule_8h | self.schedule_14h).get_next_schedule()
        self.assertEqual(schedule, self.schedule_8h)
        self.assertEqual(departure.hour, 8)

    @freeze_time("2026-06-17 10:00:00")
    def test_past_slot_is_skipped(self):
        """At 10:00, the 08:00 slot is in the past; 14:00 is returned."""
        schedule, departure = (self.schedule_8h | self.schedule_14h).get_next_schedule()
        self.assertEqual(schedule, self.schedule_14h)
        self.assertEqual(departure.hour, 14)

    @freeze_time("2026-06-17 07:00:00")
    def test_timezone_shifts_opening_hours(self):
        """08:00 Paris (CEST +2) = 06:00 UTC, already past at 07:00 UTC.
        So 14:00 Paris = 12:00 UTC is the next reachable slot.
        """
        schedule, departure = (self.schedule_8h | self.schedule_14h).get_next_schedule(
            tz="Europe/Paris"
        )
        self.assertEqual(schedule, self.schedule_14h)
        self.assertEqual(departure.hour, 12)

    def test_empty_recordset_returns_false(self):
        """No schedules → no departure."""
        schedule, departure = self.env["delivery.schedule"].get_next_schedule()
        self.assertFalse(schedule)
        self.assertFalse(departure)

    @freeze_time("2026-06-17 07:00:00")
    def test_closed_day_jumps_to_next_open_day(self):
        """Saturday schedule skips Wed/Thu/Fri; next slot is Saturday 2026-06-20."""
        # Wed 17 → Thu 18 → Fri 19 → Sat 20 (first open day)
        schedule, departure = self.schedule_sat.get_next_schedule()
        self.assertEqual(schedule, self.schedule_sat)
        self.assertEqual(departure.day, 20)  # Saturday 2026-06-20
        self.assertEqual(departure.hour, 9)  # opens at 09:00 UTC

    @freeze_time("2026-06-17 07:00:00")
    def test_horizon_too_short_returns_false(self):
        """Horizon limits the search window: Saturday (offset 3) is out of range(2).

        Default horizon is 8 days (company setting). Passing horizon=2 means
        only Wed 17 (offset 0) and Thu 18 (offset 1) are checked — no Saturday.
        """
        schedule, departure = self.schedule_sat.get_next_schedule(horizon=2)
        self.assertFalse(schedule)
        self.assertFalse(departure)

    @freeze_time("2026-06-17 07:00:00")
    def test_partner_only_searches_its_own_schedules(self):
        """Partner.get_next_schedule() is bounded by partner.delivery_schedule_ids.

        self.partner has schedule_8h and schedule_14h, but NOT schedule_sat.
        Even if schedule_sat exists in the system, it must never be returned
        for this partner — only its explicitly assigned schedules are candidates.
        """
        # Sanity check: schedule_sat is not assigned to this partner
        self.assertNotIn(self.schedule_sat, self.partner.delivery_schedule_ids)

        schedule, departure = self.partner.get_next_schedule()
        self.assertEqual(schedule, self.schedule_8h)

    @freeze_time("2026-06-17 07:00:00")
    def test_company_horizon_is_the_default(self):
        """When horizon is not passed explicitly, the company setting is used."""
        self.env.company.delivery_schedule_departure_horizon = 2
        # Saturday is 3 days away — outside the company horizon of 2
        _, departure = self.schedule_sat.get_next_schedule()
        self.assertFalse(departure)
