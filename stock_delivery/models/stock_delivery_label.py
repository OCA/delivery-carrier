# -*- coding: utf-8 -*-
# © 2016-TODAY LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, fields


class StockDeliveryLabel(models.Model):
    _name = 'stock.delivery.label'
    _description = 'Stock Delivery Label'

    picking_id = fields.Many2one(
        string='Stock Picking',
        comodel_name='stock.picking',
        related='group_id.picking_id',
    )
    pack_id = fields.Many2one(
        string='Delivery Package',
        comodel_name='stock.delivery.pack',
        related='group_id.pack_id',
    )
    group_id = fields.Many2one(
        string='Delivery Group',
        comodel_name='stock.delivery.group',
        related='rate_id.group_id',
    )
    date_generated = fields.Datetime(
        required=True,
        default=lambda s: fields.Datetime.now(),
    )
    rate_id = fields.Many2one(
        string='Rate',
        comodel_name='stock.delivery.rate',
    )
    rate = fields.Float(
        string='Cost',
        related='rate_id.rate',
    )
    currency_id = fields.Many2one(
        string='Currency',
        comodel_name='res.currency',
        related='rate_id.rate_currency_id',
    )
    img_label = fields.Binary(
        attachment=True,
        required=True,
    )
    service_id = fields.Many2one(
        string='Carrier Service',
        comodel_name='delivery.carrier',
        related='rate_id.service_id',
    )
    partner_id = fields.Many2one(
        string='Carrier Company',
        comodel_name='res.partner',
        related='service_id.partner_id',
    )
    state = fields.Selection([
        ('valid', 'Valid'),
        ('cancel', 'Cancelled'),
    ],
        default='valid',
    )
