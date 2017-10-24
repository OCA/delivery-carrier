# -*- coding: utf-8 -*-
# Copyright 2016-2017 LasLabs Inc.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import api, fields, models
from odoo.addons import decimal_precision as dp


class DeliveryPackage(models.Model):
    _name = 'delivery.package'
    _description = 'Delivery Package'

    name = fields.Char(
        required=True,
    )
    code = fields.Char(
        required=True,
        default=lambda s: s._default_code(),
    )
    package_type = fields.Selection([
        ('box', 'Box'),
        ('envelope', 'Envelope'),
        ('pallet', 'Pallet'),
    ])
    weight_tare = fields.Float(
        string='Container Weight',
        digits=dp.get_precision('Stock Weight'),
        help='The weight of the shipping container.',
    )
    weight_max = fields.Float(
        string='Max Weight',
        digits=dp.get_precision('Stock Weight'),
        help='The maximum rated weight for this container.',
    )
    product_id = fields.Many2one(
        string='Product',
        comodel_name='product.product',
        ondelete='restrict',
        help='Relating this container to a product can allow for the '
             'purchase of new containers using standard Odoo mechanisms.',
    )
    length = fields.Float(
        digits=dp.get_precision('Stock Weight'),
    )
    length_uom_id = fields.Many2one(
        string='Length Unit',
        comodel_name='product.uom',
        required=True,
        domain=lambda s: [
            ('category_id', '=',
             s.env.ref('product.uom_categ_length').id)
        ],
        default=lambda s: s.env['res.lang'].default_uom_by_category(
            'Length / Distance',
        ),
    )
    width = fields.Float(
        digits=dp.get_precision('Stock Weight'),
    )
    width_uom_id = fields.Many2one(
        string='Width Unit',
        comodel_name='product.uom',
        required=True,
        domain=lambda s: [
            ('category_id', '=',
             s.env.ref('product.uom_categ_length').id)
        ],
        default=lambda s: s.env['res.lang'].default_uom_by_category(
            'Length / Distance',
        ),
    )
    height = fields.Float(
        digits=dp.get_precision('Stock Weight'),
    )
    height_uom_id = fields.Many2one(
        string='Height Unit',
        comodel_name='product.uom',
        required=True,
        domain=lambda s: [
            ('category_id', '=',
             s.env.ref('product.uom_categ_length').id)
        ],
        default=lambda s: s.env['res.lang'].default_uom_by_category(
            'Length / Distance',
        ),
    )
    weight = fields.Float(
        string='Empty Package Weight',
        digits=dp.get_precision('Stock Weight'),
        help='Weight of the empty package.',
    )
    weight_uom_id = fields.Many2one(
        string='Weight Unit',
        comodel_name='product.uom',
        domain=lambda s: [
            ('category_id', '=',
             s.env.ref('product.product_uom_categ_kgm').id)
        ],
        default=lambda s: s.env['res.lang'].default_uom_by_category('Weight'),
    )
    active = fields.Boolean(
        default=True,
    )

    _sql_constraints = [
        ('name_uniq', 'UNIQUE(name)', 'Name must be unique.')
    ]

    @api.multi
    def name_get(self):
        names = []
        for rec in self:
            name = '%s [%s x %s x %s]' % (
                rec.name,
                rec.length,
                rec.width,
                rec.height,
            )
            names.append((rec.id, name))
        return names

    @api.model
    def _default_code(self):
        return self.env['ir.sequence'].next_by_code(
            'stock_picking_delivery.ir_sequence_delivery_package',
        )
