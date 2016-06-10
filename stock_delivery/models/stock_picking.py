# -*- coding: utf-8 -*-
# © 2016-TODAY LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, fields, api


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    number_of_packages = fields.Integer(
        string='Number of Packages',
        compute=lambda s: s._compute_delivery_packages(),
    )
    delivery_pack_ids = fields.One2many(
        string='Delivery Package',
        comodel_name='stock.delivery.pack',
        compute=lambda s: s._compute_delivery_packages(),
    )
    delivery_group_ids = fields.One2many(
        string='Delivery Groups',
        comodel_name='stock.delivery.group',
        inverse_name='picking_id',
    )

    @api.multi
    def _compute_delivery_packages(self):
        for rec_id in self:
            rec_id.delivery_pack_ids = [
                g.pack_id.id for g in rec_id.delivery_group_ids
            ]
            rec_id.number_of_packages = len(rec_id.delivery_pack_ids)

    @api.multi
    def put_in_pack(self):
        package_id_int = super(StockPicking, self).put_in_pack()
        if package_id_int:
            pack_op_ids = self.env['stock.pack.operation'].search([
                ('result_package_id', '=', package_id_int),
            ])
            rec_id = self.env['stock.delivery.new'].create({
                'quant_pack_id': package_id_int,
                'pack_operation_ids': [(6, 0, [o.id for o in pack_op_ids])],
                'picking_ids': [(6, 0, [p.id for p in self])],
            })
            return rec_id.action_show_wizard()
