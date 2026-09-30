# Copyright 2018 Tecnativa - Sergio Teruel
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from datetime import datetime, timedelta

import pytz

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class DeliverySchedule(models.Model):
    _name = "delivery.schedule"
    _description = "Delivery Schedule"

    name = fields.Char(required=True)
    color = fields.Integer(string="Color Index")
    hour_from = fields.Float(string="From")
    hour_to = fields.Float(string="To", default=24.00, required=True)
    monday = fields.Boolean(default=True)
    tuesday = fields.Boolean(default=True)
    wednesday = fields.Boolean(default=True)
    thursday = fields.Boolean(default=True)
    friday = fields.Boolean(default=True)
    saturday = fields.Boolean()
    sunday = fields.Boolean()

    @api.constrains("hour_from", "hour_to")
    def _check_hour_interval(self):
        if (
            self.hour_from < 0.0
            or self.hour_to > 24.0
            or self.hour_from >= self.hour_to
        ):
            raise ValidationError(
                self.env._(
                    "Error ! You can not set hour_from greater or equal "
                    "than hour_to ."
                )
            )
        return True

    @api.constrains(
        "monday",
        "tuesday",
        "wednesday",
        "thursday",
        "friday",
        "saturday",
        "sunday",
    )
    def _check_day_selected(self):
        if not any([self[x[0]] for x in self._days_of_week()]):
            raise ValidationError(
                self.env._("Error ! You must set one day to delivery.")
            )

    def _days_of_week(self):
        return [
            ("monday", self.env._("Monday")),
            ("tuesday", self.env._("Tuesday")),
            ("wednesday", self.env._("Wednesday")),
            ("thursday", self.env._("Thursday")),
            ("friday", self.env._("Friday")),
            ("saturday", self.env._("Saturday")),
            ("sunday", self.env._("Sunday")),
        ]

    @api.depends(
        "hour_from",
        "hour_to",
        "monday",
        "tuesday",
        "wednesday",
        "thursday",
        "friday",
        "saturday",
        "sunday",
    )
    def _compute_display_name(self):
        for schedule in self:
            hour_from = "{:02.0f}:{:02.0f}".format(*divmod(schedule.hour_from * 60, 60))
            hour_to = "{:02.0f}:{:02.0f}".format(*divmod(schedule.hour_to * 60, 60))
            days_accepted = [
                d[1][:2] for d in schedule._days_of_week() if schedule[d[0]]
            ]
            days = (
                ", ".join(days_accepted)
                if days_accepted and len(days_accepted) < 7
                else self.env._("All days")
            )
            schedule.display_name = f"{hour_from}-{hour_to} ({days})"

    def get_next_schedule(self, from_date=None, tz=None, horizon=None):
        """Return the closiest schedule and departure datetime from date.

        :param from_date: UTC-naive datetime anchor; defaults to now()
        :param tz: IANA timezone string for local-time conversion
        :param horizon: days ahead to search; defaults to company setting
        """
        pairs = self._scheduled_departures(from_date=from_date, tz=tz, horizon=horizon)
        if not pairs:
            return self.env["delivery.schedule"], False
        return pairs[0]

    def _scheduled_departures(self, from_date=None, tz=None, horizon=None):
        """All (schedule, UTC-naive departure) pairs within horizon days, sorted.

        Only departures strictly after from_date are included.
        DST (Daylight Saving Time) transitions are handled correctly.

        :param from_date: UTC-naive datetime anchor; defaults to now()
        :param tz: IANA timezone string for local-time conversion
        :param horizon: days ahead to search; defaults to company setting
        """
        if not from_date:
            from_date = fields.Datetime.now()
        if not horizon:
            horizon = self.env.company.delivery_schedule_departure_horizon
        if not tz:
            tz = self.env.user.tz or self.env.company.tz or "UTC"
        local_zone = pytz.timezone(tz)
        local_reference = pytz.utc.localize(from_date).astimezone(local_zone)
        candidates = []
        for day_offset in range(horizon):
            local_date = (local_reference + timedelta(days=day_offset)).date()
            for schedule in self:
                weekday_field = schedule._days_of_week()[local_date.weekday()][0]
                if not schedule[weekday_field]:
                    continue
                local_naive = datetime(
                    local_date.year, local_date.month, local_date.day
                ) + timedelta(hours=schedule.hour_from)
                departure = (
                    local_zone.localize(local_naive)
                    .astimezone(pytz.utc)
                    .replace(tzinfo=None)
                )
                if departure > from_date:
                    candidates.append((schedule, departure))
        candidates.sort(key=lambda pair: pair[1])
        return candidates
