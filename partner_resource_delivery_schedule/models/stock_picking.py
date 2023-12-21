# Copyright 2023 Moduon Team S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)

from datetime import datetime, timedelta

from odoo import fields, models

from .helpers import get_next_available_date


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def _get_commitment_date_resources_and_calendars(self):
        """Resources and Calendars for taking in consderation
        for commitment date calculation of a picking."""
        resources = self.env["resource.resource"].browse()
        calendars = self.mapped("company_id.resource_calendar_id")
        sr_partner = self.partner_id.filtered("delivery_schedule_resource_id")
        if sr_partner:
            resources = sr_partner.mapped("delivery_schedule_resource_id")
            calendars |= sr_partner.mapped("delivery_schedule_calendar_id")
        return resources, calendars

    def _create_backorder(self):
        """When a backorder is created, recompute commitment date for the new
        picking if scheduled_date it's in the past."""
        backorders = super()._create_backorder()
        interval_days = int(
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("partner_resource_delivery_schedule.interval_days", 60)
        )
        for backorder in backorders:
            if fields.Date.today() >= backorder.scheduled_date.date():
                tomorrow = datetime.combine(
                    fields.Date.today(), datetime.min.time()
                ) + timedelta(days=1)
                # Calc commitment date for the new picking
                (
                    resources,
                    calendars,
                ) = backorder._get_commitment_date_resources_and_calendars()
                next_available_date = get_next_available_date(
                    tomorrow,
                    tomorrow + timedelta(days=interval_days),
                    resources=resources,
                    calendars=calendars,
                )
                # Set tomorrow if no date found because maybe tomorrow can send it
                backorder.scheduled_date = next_available_date or tomorrow
        return backorders
