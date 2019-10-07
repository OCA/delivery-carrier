# -*- coding: utf-8 -*-
# Copyright 2017 LasLabs Inc.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import fields, models


class StockPicking(models.Model):

    _inherit = 'stock.picking'

    dispatch_rate_ids = fields.One2many(
        string='Dispatch Rates',
        comodel_name='stock.picking.rate',
        inverse_name='picking_id',
    )
