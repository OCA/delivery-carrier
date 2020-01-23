# Copyright 2018 Tecnativa - Sergio Teruel
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import _, api, fields, models
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
                _(
                    "Error ! You can not set hour_from greater or equal "
                    "than hour_to ."
                )
            )
        return True

    @api.constrains(
        "monday",
        "tuesday",
        "wednesday",
        "wednesday",
        "thursday",
        "friday",
        "saturday",
        "sunday",
    )
    def _check_day_selected(self):
        if not any([self[x[0]] for x in self._days_of_week()]):
            raise ValidationError(_("Error ! You must set one day to delivery."))
        return True

    def _days_of_week(self):
        return [
            ("monday", _("Monday")),
            ("tuesday", _("Tuesday")),
            ("wednesday", _("Wednesday")),
            ("thursday", _("Thursday")),
            ("friday", _("Friday")),
            ("saturday", _("Saturday")),
            ("sunday", _("Sunday")),
        ]

    def name_get(self):
        result = []
        for schedule in self:
            hour_from = "{:02.0f}:{:02.0f}".format(*divmod(schedule.hour_from * 60, 60))
            hour_to = "{:02.0f}:{:02.0f}".format(*divmod(schedule.hour_to * 60, 60))
            days_accepted = [d[1][:2] for d in self._days_of_week() if schedule[d[0]]]
            days = (
                days_accepted
                and len(days_accepted) > 0
                and len(days_accepted) < 7
                and ", ".join(days_accepted)
                or _("All days")
            )
            result.append(
                (
                    schedule.id,
                    "{hour_from}-{hour_to} ({days})".format(
                        hour_from=hour_from, hour_to=hour_to, days=days
                    ),
                )
            )
        return result
