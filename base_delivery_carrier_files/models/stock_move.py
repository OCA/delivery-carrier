# -*- coding: utf-8 -*-
# Copyright 2012 Camptocamp SA
# Author: Guewen Baconnier
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, api


class StockMove(models.Model):
    _inherit = 'stock.move'

    @api.multi
    def write(self, values):
        write_result = super(StockMove, self).write(values)
        if values.get('state') and values['state'] == 'done':
            picking_ids = map(lambda p: p.id, self.mapped('picking_id'))
            done_pickings = self.env['stock.picking'].search([
                ('id', 'in', picking_ids),
                ('state', '=', 'done')
            ])
            if done_pickings:
                done_pickings.generate_carrier_files()
        return write_result
