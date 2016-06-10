# -*- coding: utf-8 -*-
# © 2016-TODAY LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, fields, api


OPERATION_STATES = [
    ('unknown', 'Unknown'),
    ('pre_transit', 'Pre Transit'),
    ('in_transit', 'In Transit'),
    ('out_for_delivery', 'Out For Delivery'),
    ('delivered', 'Delivered'),
    ('available_for_pickup', 'Available For Pickup'),
    ('return_to_sender', 'Return To Sender'),
    ('fail', 'Failure'),
    ('cancel', 'Cancelled'),
    ('error', 'Error'),
]


class StockDeliveryOperation(models.Model):
    _name = 'stock.delivery.operation'
    _description = 'Stock Delivery Operation'

    group_id = fields.Many2one(
        string='Delivery Group',
        comodel_name='stock.delivery.group',
        required=True,
    )
    picking_id = fields.Many2one(
        string='Stock Picking',
        comodel_name='stock.picking',
        related='group_id.picking_id',
    )
    location_id = fields.Many2one(
        string='Location',
        comodel_name='stock.delivery.location',
        related='picking_id.location_id'
    )
    state = fields.Selection(
        OPERATION_STATES,
        required=True,
        default='unknown',
    )
    date_updated = fields.Datetime(
        required=True,
        default=lambda s: fields.Datetime.now(),
    )
    service_id = fields.Many2one(
        string='Carrier Service',
        comodel_name='delivery.carrier',
        related='picking_id.carrier_id',
    )
    partner_id = fields.Many2one(
        string='Carrier Company',
        comodel_name='res.partner',
        related='service_id.partner_id',
    )
    carrier_ref = fields.Char()

    @api.multi
    def name_get(self):
        res = []
        for rec_id in self:
            name = '[{date}] {state}'.format(
                date=rec_id.date_updated,
                state=rec_id.state,
            )
            res.append((rec_id.id, name))
        return res
