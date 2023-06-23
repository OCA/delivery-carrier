# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
import psycopg2

from odoo import api, fields, models, registry, SUPERUSER_ID, _

_logger = logging.getLogger(__name__)


class ResourceCalendarAttendanceInherit(models.Model):
    _inherit = 'resource.calendar.attendance'

    hour_delay = fields.Float('Time', required=True)
    select_type_delay = fields.Selection([('hour', 'Hour(s)'), ('day', 'Day(s)'), ('week', 'Week(s)')], required=True, default='hour')

    