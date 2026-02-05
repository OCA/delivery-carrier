# Copyright 2026 NICO SOLUTINS - ENGINEERING& IT (https://nnico-solutions.de).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import datetime

from odoo import fields

from odoo.addons.base.tests.common import BaseCommon


class TestStockPicking(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.partner = cls.env["res.partner"].create(
            {
                "name": "Test Partner",
            }
        )

        cls.schedule_monday = cls.env["delivery.schedule"].create(
            {
                "name": "Monday 09-10",
                "hour_from": 9.0,
                "hour_to": 10.0,
                "monday": True,
            }
        )

        cls.schedule_tuesday = cls.env["delivery.schedule"].create(
            {
                "name": "Tuesday 13-14",
                "hour_from": 13.0,
                "hour_to": 14.0,
                "tuesday": True,
            }
        )

        cls.partner.delivery_schedule_ids = [
            (4, cls.schedule_monday.id),
            (4, cls.schedule_tuesday.id),
        ]

        cls.picking_type_out = cls.env.ref("stock.picking_type_out")

    def setUp(self):
        super().setUp()
        self.picking = self.env["stock.picking"].create(
            {
                "partner_id": self.partner.id,
                "picking_type_id": self.picking_type_out.id,
                "scheduled_date": fields.Datetime.to_string(
                    datetime.datetime(2026, 2, 2, 8, 0, 0)
                ),
            }
        )

    def _set_scheduled_date(self, naive_dt):
        """Set scheduled_date using naive datetime (partner local time)"""
        self.picking.scheduled_date = fields.Datetime.to_string(naive_dt)

    def test_no_warning_for_in_schedule_date(self):
        dt = datetime.datetime(2026, 2, 2, 9, 0, 0)
        self._set_scheduled_date(dt)
        dt_str = fields.Datetime.to_string(dt)
        self.assertTrue(self.partner.allow_delivery_date(dt_str))
        self.assertEqual(self.picking.partner_delivery_schedule_warning, "")

    def test_warning_for_out_of_schedule_date(self):
        dt = datetime.datetime(2026, 2, 7, 10, 0, 0)  # Sonntag
        self._set_scheduled_date(dt)
        dt_str = fields.Datetime.to_string(dt)
        self.assertFalse(self.partner.allow_delivery_date(dt_str))
        warning = self.picking.partner_delivery_schedule_warning
        self.assertTrue(warning)
        self.assertIn("09:00-10:00", warning)
        self.assertIn("13:00-14:00", warning)

    def test_warning_at_hour_boundaries(self):
        start = datetime.datetime(2026, 2, 2, 9, 0, 0)
        self._set_scheduled_date(start)
        self.assertTrue(
            self.partner.allow_delivery_date(fields.Datetime.to_string(start))
        )
        end = datetime.datetime(2026, 2, 2, 10, 0, 0)
        self._set_scheduled_date(end)
        self.assertFalse(
            self.partner.allow_delivery_date(fields.Datetime.to_string(end))
        )

    def test_warning_for_wrong_weekday(self):
        dt = datetime.datetime(2026, 2, 4, 10, 0, 0)
        self._set_scheduled_date(dt)
        dt_str = fields.Datetime.to_string(dt)
        self.assertFalse(self.partner.allow_delivery_date(dt_str))
        self.assertTrue(self.picking.partner_delivery_schedule_warning)
