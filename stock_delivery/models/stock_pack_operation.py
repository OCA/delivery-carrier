# -*- coding: utf-8 -*-
# © 2016-TODAY LasLabs Inc.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, api


class StockPackOperation(models.Model):
    _inherit = 'stock.pack.operation'

    @api.multi
    def save(self):
        res = super(StockPackOperation, self).save()
        if not self.result_package_id:
            return res
        wizard_obj = self.env['stock.delivery.new'].with_context({
            'active_ids': [r.id for r in self],
        })
        wizard_id = wizard_obj.create({
            'quant_pack_id': self.result_package_id.id,
        })
        return wizard_id.action_show_wizard()
