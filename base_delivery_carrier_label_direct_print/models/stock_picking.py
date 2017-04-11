# -*- coding: utf-8 -*-
# © 2017 Angel Moya (PESOL)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openerp import models, api


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.multi
    def get_shipping_label_values(self, label):
        result = super(StockPicking, self).get_shipping_label_values(label)
        if self.carrier_id:
            result.update({'direct_print': self.carrier_id.direct_print,
                           'no_attach': self.carrier_id.no_attach,
                           'printer_id': self.carrier_id.printer_id})
        return result
