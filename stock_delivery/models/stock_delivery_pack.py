# -*- coding: utf-8 -*-
# © 2016-TODAY LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, fields, api


class StockDeliveryPack(models.Model):
    _name = 'stock.delivery.pack'
    _description = 'Stock Delivery Pack'
    _inherit = 'stock.delivery.pack.template'
    _inherits = {'stock.quant.package': 'quant_pack_id'}

    group_id = fields.Many2one(
        name='Delivery Group',
        comodel_name='stock.delivery.group',
    )
    pack_template_id = fields.Many2one(
        name='Package Template',
        comodel_name='stock.delivery.pack.template',
    )
    quant_pack_id = fields.Many2one(
        name='Quant Pack',
        comodel_name='stock.quant.package',
        ondelete='restrict',
        required=True,
    )
    pack_operation_ids = fields.Many2many(
        string='Pack Operations',
        comodel_name='stock.pack.operation',
        readonly=True,
    )

    @api.onchange('pack_template_id')
    def _onchange_pack_template_id(self):
        if not self.pack_template_id:
            return None
        for key, val in self.pack_template_id.read()[0].iteritems():
            if key == 'id':
                continue
            setattr(self, key, val)

    @api.model
    def create(self, vals):
        """ Hard code usage of quant pack name, instead of delivery pack """
        vals['name'] = self.env['stock.quant.package'].browse(
            vals['quant_pack_id']
        ).name
        return super(StockDeliveryPack, self).create(vals)
