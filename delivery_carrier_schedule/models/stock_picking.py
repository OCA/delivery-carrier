# Copyright 2023 Moduon Team S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)

from odoo import models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def _get_expected_date_resources_and_calendars(self):
        """Resources and Calendars for taking in consderation
        for expected date calculation of a picking."""
        resources, calendars = super()._get_expected_date_resources_and_calendars()
        resources |= self.carrier_id.resource_id
        return resources, calendars
