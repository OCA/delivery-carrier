# -*- coding: utf-8 -*-
# Copyright 2017 LasLabs Inc.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import api, fields, models


class DeliveryCarrierRate(models.Model):

    _name = 'delivery.carrier.rate'
    _description = 'Delivery Carrier Rate'
    _inherit = 'stock.picking.rate'
    _sql_constraints = [(
        'sale_order_service_uniq',
        'unique (sale_order_id, service_id)',
        'A sale order can only have one delivery rate per carrier',
    )]

    picking_id = fields.Many2one(
        string='Stock Picking',
        required=False,
    )
    sale_order_id = fields.Many2one(
        string='Sale Order',
        comodel_name='sale.order',
        required=True,
    )

    @api.multi
    def generate_equiv_picking_rates(self, stock_picking):
        stock_picking.ensure_one()
        for record in self:
            record_data = record.copy_data()[0]
            del record_data['sale_order_id']
            record_data['picking_id'] = stock_picking.id
            self.env['stock.picking.rate'].create(record_data)
