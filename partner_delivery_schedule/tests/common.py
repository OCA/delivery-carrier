# Copyright 2026 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.addons.base.tests.common import BaseCommon


class DeliveryScheduleCommon(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Force user timezone to UTC so test assertions on departure hours are
        # environment-independent (get_next_schedule uses env.user.tz first).
        cls.env.user.tz = "UTC"
        cls._setup_schedules()
        cls._setup_partners()

    @classmethod
    def _setup_schedules(cls):
        Schedule = cls.env["delivery.schedule"]
        cls.schedule_8h = Schedule.create(
            {
                "name": "08h00",
                "hour_from": 8.0,
                "hour_to": 10.0,
            }
        )
        cls.schedule_14h = Schedule.create(
            {
                "name": "14h00",
                "hour_from": 14.0,
                "hour_to": 16.0,
            }
        )
        cls.schedule_sat = Schedule.create(
            {
                "name": "Saturday",
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

    @classmethod
    def _setup_partners(cls):
        cls.partner = cls.env["res.partner"].create(
            {
                "name": "Test Partner",
                "tz": "UTC",
                "delivery_schedule_ids": [
                    (4, cls.schedule_8h.id),
                    (4, cls.schedule_14h.id),
                ],
            }
        )
