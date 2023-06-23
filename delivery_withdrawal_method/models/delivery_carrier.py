# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
import psycopg2

from odoo import api, fields, models, registry, SUPERUSER_ID, _

_logger = logging.getLogger(__name__)


class DeliveryCarrierInherit(models.Model):
    _inherit = 'delivery.carrier'

    number_delivery_period = fields.Integer()

    select_delivery_period = fields.Selection(
        [
            ("day", "Day(s)"),
            ("week", "Week(s)"),
            ("month", "Month(s)"),
        ],
        default="day"
    )

    is_withdrawal_point = fields.Boolean("Is a withdrawal point ?", default=False)

    withdrawal_point_ids = fields.One2many('delivery.withdrawal.point', 'point_id', copy=True)
