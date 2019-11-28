# Copyright 2018 Tecnativa - Sergio Teruel
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.exceptions import ValidationError
from odoo.tests import SavepointCase


class TestStockPikingReturnRefundOption(SavepointCase):
    at_install = False
    post_install = True

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
        cls.schedule2 = cls.env["delivery.schedule"].create(
            {
                "name": "test2",
                "hour_from": 10,
                "hour_to": 12,
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
                "delivery_schedule_ids": [(6, 0, cls.schedule.ids + cls.schedule2.ids)],
            }
        )

    def test_partner_schedule_name(self):
        self.assertEqual(self.schedule.name_get()[0][1], "08:00-10:00 (Mo, Tu)")

        day_update = {}
        for day in self.schedule._days_of_week():
            day_update[day[0]] = True
        self.schedule.update(day_update)
        self.assertEqual(self.schedule.name_get()[0][1], "08:00-10:00 (All days)")

        with self.assertRaises(ValidationError):
            self.schedule.update({"hour_from": 0, "hour_to": 25})

        day_update = {}
        for day in self.schedule._days_of_week():
            day_update[day[0]] = False
        with self.assertRaises(ValidationError):
            self.schedule.update(day_update)

    def test_partner_allow_delivery(self):
        self.assertTrue(self.partner.allow_delivery_date("2018-09-03 09:00:00"))
        self.assertTrue(self.partner.allow_delivery_date("2018-09-04 09:00:00"))
        self.assertFalse(self.partner.allow_delivery_date("2018-09-04 12:01:00"))
        self.assertFalse(self.partner.allow_delivery_date("2018-09-05 10:01:00"))

        # Allow delivery in all days
        day_update = {}
        for day in self.schedule._days_of_week():
            day_update[day[0]] = True
        self.schedule.update(day_update)
        self.assertTrue(self.partner.allow_delivery_date("2018-09-09 09:00:00"))
