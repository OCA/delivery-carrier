# Copyright 2026 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ResCompany(models.Model):
    _inherit = "res.company"

    delivery_schedule_departure_horizon = fields.Integer(
        string="Delivery Departure Horizon (days)",
        default=8,
        help="Number of days ahead to search for the next reachable "
        "departure when using delivery schedules.",
    )

    @api.constrains("delivery_schedule_departure_horizon")
    def _check_departure_horizon(self):
        for company in self:
            if company.delivery_schedule_departure_horizon < 1:
                raise ValidationError(
                    self.env._("Delivery departure horizon must be at least 1 day.")
                )
