# coding: utf-8
# Copyright (C) 2018 - Today: GRAP (http://www.grap.coop)
# @author: Sylvain LE GAL (https://twitter.com/legalsylvain)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models


class StockMove(models.Model):
    _inherit = 'stock.move'

    def _prepare_picking_assign(self, cr, uid, move, context=None):
        res = super(StockMove, self)._prepare_picking_assign(
            cr, uid, move, context=context
        )
        res.update({
            'final_shipping_partner_id':
            move.group_id.final_shipping_partner_id.id,
        })
        return res
