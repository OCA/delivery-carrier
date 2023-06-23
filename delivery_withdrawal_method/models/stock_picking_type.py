# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
import psycopg2

from odoo import api, fields, models, registry, SUPERUSER_ID, _

_logger = logging.getLogger(__name__)


class StockPickingTypeInherit(models.Model):
    _inherit = 'stock.picking.type'

    code = fields.Selection(selection_add=[
        ('withdrawal', 'Withdrawal')
    ], ondelete={'withdrawal': 'cascade'})
