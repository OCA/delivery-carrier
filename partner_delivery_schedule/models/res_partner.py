# Copyright 2018 Tecnativa - Sergio Teruel
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    delivery_schedule_ids = fields.Many2many(
        comodel_name="delivery.schedule",
        column1="partner_id",
        column2="delivery_schedule_id",
        string="Delivery Schedule",
    )

    def allow_delivery_date(self, date_str):
        """
        Help method that returns if a partner allow delivery goods in
        requested date (with time)
        """
        day_list = self.env["delivery.schedule"]._days_of_week()
        date = fields.Datetime.from_string(date_str)
        week_day = day_list[date.weekday()][0]
        request_delivery_hour = int(date.hour) + float(date.minute / 60)
        delivery_records = self.delivery_schedule_ids.filtered(
            lambda x: (
                x[week_day]
                and request_delivery_hour >= x.hour_from
                and request_delivery_hour < x.hour_to
            )
        )
        return bool(delivery_records)
