# -*- coding: utf-8 -*-
# Copyright 2016-2017 LasLabs Inc.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import api, fields, models
from odoo.addons import decimal_precision as dp


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.multi
    def do_new_dispatch(self):
        self.ensure_one()
        if not self.dispatch_rate_ids:
            self.action_compute_rates()
        wizard = self.env['stock.picking.delivery'].create({
            'picking_id': self.id,
        })
        action = wizard.get_formview_action()
        action['target'] = 'new'
        return action
