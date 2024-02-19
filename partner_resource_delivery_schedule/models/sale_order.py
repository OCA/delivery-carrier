# Copyright 2023 Moduon Team S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)

from datetime import datetime, timedelta

from odoo import _, exceptions, fields, models

from .helpers import get_next_available_date


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _get_commitment_date_resources_and_calendars(self):
        """Resources and Calendars for taking in consderation
        for commitment date calculation of an order."""
        resources = self.env["resource.resource"].browse()
        calendars = self.mapped("company_id.resource_calendar_id")
        sr_partner = (self.partner_shipping_id or self.partner_id).filtered(
            "delivery_schedule_resource_id"
        )
        if sr_partner:
            resources = sr_partner.mapped("delivery_schedule_resource_id")
            calendars |= sr_partner.mapped("delivery_schedule_calendar_id")
        return resources, calendars

    def calc_next_commitment_date(self):
        """Calculate the next commitment date for the order."""
        self.ensure_one()
        interval_days = int(
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("partner_resource_delivery_schedule.interval_days", 60)
        )

        # Choose date_start
        if self.commitment_date:
            date_start = self.commitment_date
        elif self.expected_date:
            date_start = self.expected_date - timedelta(days=1)
            # Increased after when choosing next day (will match expected_date)
        else:
            # Raise Exception because we would expect at least expected_date
            raise exceptions.UserError(
                _(
                    "Commitment date or expected date "
                    "is required to calculate the next commitment date"
                )
            )
        # Set now() if date_start is in the past
        if date_start.date() <= fields.date.today():
            date_start = fields.datetime.now()
        # Choose next day after date_start
        date_start = datetime.combine(
            date_start.date(), datetime.min.time()
        ) + timedelta(days=1)

        # Get next available date
        (
            resources,
            calendars,
        ) = self._get_commitment_date_resources_and_calendars()
        next_available_date = get_next_available_date(
            date_start,
            date_start + timedelta(days=interval_days),
            resources=resources,
            calendars=calendars,
        )
        if not next_available_date:
            raise exceptions.UserError(
                _(
                    "No available date found for commitment date "
                    "in the next %(interval_days)s days since %(date_start)s.",
                    interval_days=interval_days,
                    date_start=date_start,
                )
            )
        self.commitment_date = next_available_date
