# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields


class WebsiteWithdrawalSaleOrder(models.Model):
    _inherit = 'sale.order'

    picking_type_id = fields.Many2one('stock.picking.type', 'Operation Type')

    def write(self, values):
        res = super(WebsiteWithdrawalSaleOrder, self).write(values)
        if values.get('picking_type_id'):
            self.order_line.move_ids.picking_type_id = values.get('picking_type_id')
        return res


class WebsiteWithdrawalSaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    def _prepare_procurement_values(self, group_id=False):
        res = super(WebsiteWithdrawalSaleOrderLine, self)._prepare_procurement_values(group_id)
        res['picking_type_id'] = self.order_id.picking_type_id.id
        return res