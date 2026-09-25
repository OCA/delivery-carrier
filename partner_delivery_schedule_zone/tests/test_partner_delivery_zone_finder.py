# Copyright 2026 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from freezegun import freeze_time

from odoo import fields
from odoo.tests import tagged

from .common import DeliveryZoneScheduleCommon


@tagged("post_install", "-at_install")
class TestZoneFindNextSchedule(DeliveryZoneScheduleCommon):
    @freeze_time("2026-06-09 06:00:00")
    def test_earliest_slot_is_returned(self):
        """Before 08:00, the 08:00 slot wins over 14:00."""
        schedule, departure = self.delivery_zone_a.get_next_schedule()
        self.assertEqual(schedule, self.schedule_8h)
        self.assertGreater(departure, fields.Datetime.now())

    def test_single_schedule_zone_returns_it(self):
        """Zone with one schedule always returns that schedule."""
        schedule, departure = self.delivery_zone_b.get_next_schedule()
        self.assertEqual(schedule, self.schedule_sat)
        self.assertTrue(departure)

    def test_empty_zone_returns_false(self):
        """Zone without schedules returns (empty recordset, False)."""
        schedule, departure = self.zone_empty.get_next_schedule()
        self.assertFalse(schedule)
        self.assertFalse(departure)

    @freeze_time("2026-06-09 06:00:00")
    def test_later_from_date_skips_imminent_slot(self):
        """A later from_date skips the 08:00 slot; 14:00 wins."""
        from datetime import timedelta

        # 06:00 + 240 min = 10:00 → 08:00 is unreachable, 14:00 is next
        later = fields.Datetime.now() + timedelta(minutes=240)
        schedule, departure = self.delivery_zone_a.get_next_schedule(from_date=later)
        self.assertEqual(schedule, self.schedule_14h)

    @freeze_time("2026-06-09 16:00:00")
    def test_wraps_to_next_day_after_last_slot(self):
        """After 14:00 (last slot), next departure is tomorrow at 08:00."""
        schedule, departure = self.delivery_zone_a.get_next_schedule()
        self.assertEqual(schedule, self.schedule_8h)
        self.assertEqual(departure.day, 10)  # Wednesday 2026-06-10
        self.assertEqual(departure.hour, 8)

    @freeze_time("2026-06-09 06:00:00")
    def test_timezone_shifts_opening_hours(self):
        """08:00 Europe/Paris (CEST +2) = 06:00 UTC, already past at 06:00 UTC.
        So 14:00 Paris = 12:00 UTC is the next slot.
        """
        schedule, departure = self.delivery_zone_a.get_next_schedule(tz="Europe/Paris")
        self.assertEqual(schedule, self.schedule_14h)
        self.assertEqual(departure.hour, 12)

    @freeze_time("2026-03-29 00:00:00")
    def test_dst_transition_resolved_correctly(self):
        """On spring-forward Sunday, 05:00 local (CEST +2) = 03:00 UTC."""
        sunday_schedule = self.env["delivery.schedule"].create(
            {
                "name": "Sunday early",
                "hour_from": 5.0,
                "hour_to": 9.0,
                "monday": False,
                "tuesday": False,
                "wednesday": False,
                "thursday": False,
                "friday": False,
                "saturday": False,
                "sunday": True,
            }
        )
        zone = self.env["partner.delivery.zone"].create(
            {
                "name": "DST Zone",
                "code": "DST",
                "delivery_schedule_ids": [(4, sunday_schedule.id)],
            }
        )
        schedule, departure = zone.get_next_schedule(tz="Europe/Paris")
        self.assertEqual(schedule, sunday_schedule)
        self.assertEqual(departure.hour, 3)

    @freeze_time("2026-06-08 06:00:00")
    def test_closed_day_jumps_to_next_open_day(self):
        """Schedule open only on Wednesday; Mon 08 → next slot is Wed 10."""
        wednesday_schedule = self.env["delivery.schedule"].create(
            {
                "name": "Wednesday only",
                "hour_from": 9.0,
                "hour_to": 12.0,
                "monday": False,
                "tuesday": False,
                "wednesday": True,
                "thursday": False,
                "friday": False,
                "saturday": False,
                "sunday": False,
            }
        )
        zone = self.env["partner.delivery.zone"].create(
            {
                "name": "Wednesday Zone",
                "code": "WED",
                "delivery_schedule_ids": [(4, wednesday_schedule.id)],
            }
        )
        schedule, departure = zone.get_next_schedule()
        self.assertEqual(schedule, wednesday_schedule)
        self.assertEqual(departure.day, 10)
        self.assertEqual(departure.hour, 9)

    @freeze_time("2026-06-08 06:00:00")
    def test_horizon_too_short_returns_false(self):
        """Saturday is 5 days away from Monday; horizon=2 cannot reach it."""
        saturday_schedule = self.env["delivery.schedule"].create(
            {
                "name": "Saturday only",
                "hour_from": 9.0,
                "hour_to": 12.0,
                "monday": False,
                "tuesday": False,
                "wednesday": False,
                "thursday": False,
                "friday": False,
                "saturday": True,
                "sunday": False,
            }
        )
        zone = self.env["partner.delivery.zone"].create(
            {
                "name": "Saturday Zone",
                "code": "SAT",
                "delivery_schedule_ids": [(4, saturday_schedule.id)],
            }
        )
        self.env.company.delivery_schedule_departure_horizon = 1
        schedule, departure = zone.get_next_schedule()
        self.assertFalse(schedule)
        self.assertFalse(departure)
