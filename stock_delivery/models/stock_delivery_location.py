# -*- coding: utf-8 -*-
# © 2016-TODAY LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, fields


class StockDeliveryLocation(models.Model):
    _name = 'stock.delivery.location'
    _description = 'Stock Delivery Location'

    city = fields.Char(required=True)
    zip = fields.Char(required=True)
    state_id = fields.Many2one(
        string='State',
        comodel_name='res.country.state',
        required=True,
    )
    country_id = fields.Many2one(
        string='Country',
        comodel_name='res.country',
        required=True,
    )
