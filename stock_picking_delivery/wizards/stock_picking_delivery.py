# -*- coding: utf-8 -*-
# Copyright 2016-2017 LasLabs Inc.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import _, api, fields, models


class StockPickingDelivery(models.TransientModel):
    _name = 'stock.picking.delivery'
    _description = 'Stock Picking Delivery Wizard'

    picking_id = fields.Many2one(
        string='Picking',
        comodel_name='stock.picking',
        default='_default_picking_id',
        required=True,
        readonly=True,
    )
    delivery_package_id = fields.Many2one(
        string='Delivery Package',
        comodel_name='delivery.package',
    )
    rate_ids = fields.One2many(
        string='Dispatch Rates',
        comodel_name='stock.picking.rate',
        related='picking_id.dispatch_rate_ids',
    )
    purchase_rate_id = fields.Many2one(
        string='Rate to Purchase',
        comodel_name='stock.picking.rate',
        domain="[('id', 'in', rate_ids)]",
    )
    weight_tare = fields.Float(
        string='Container Weight',
        compute='_compute_weight_tare',
    )
    weight_net = fields.Float(
        string='Net Weight',
        related='picking_id.weight',
    )
    weight_uom_id = fields.Many2one(
        string='Weight Unit',
        comodel_name='product.uom',
        related='picking_id.weight_uom_id',
        required=True,
        readonly=False,
        domain=lambda s: [
            ('category_id', '=',
             s.env.ref('product.product_uom_categ_kgm').id)
        ],
        default=lambda s: s.env['res.lang'].default_uom_by_category('Weight'),
    )
    weight_total = fields.Float(
        string='Shipping Weight',
        compute='_compute_weight_total',
    )

    @api.model
    def _default_picking_id(self):
        if self.env.context.get('active_model') == 'stock.picking':
            return self.env.context.get('active_id')

    @api.multi
    @api.depends('weight_uom_id', 'delivery_package_id.weight_uom_id')
    def _compute_weight_tare(self):
        for record in self.filtered(lambda r: r.delivery_package_id):
            uom_to = record.weight_uom_id
            uom_from = record.delivery_package_id.weight_uom_id
            weight_tare = record.delivery_package_id.weight
            if uom_to != uom_from:
                weight_tare = uom_to._compute_quantity(
                    weight_tare, uom_from,
                )
            record.weight_tare = weight_tare

    @api.multi
    @api.depends('weight_net', 'weight_tare')
    def _compute_weight_total(self):
        for record in self:
            record.weight_total = record.weight_tare + record.weight_net

    @api.multi
    def action_compute_rates(self):
        self.ensure_one()
        return self.picking_id.action_compute_rates()
