# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
import psycopg2

from odoo import api, fields, models, registry, SUPERUSER_ID, _

_logger = logging.getLogger(__name__)


class ResourceCalendarInherit(models.Model):
    _inherit = 'resource.calendar'

    is_withdrawal_working_time = fields.Boolean(string="Is withdrawal working hour ?")

