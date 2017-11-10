# -*- coding: utf-8 -*-
# Copyright 2017 LasLabs Inc.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import api, models


class StockPicking(models.Model):

    _inherit = 'stock.picking'

    @api.multi
    def send_to_shipper(self):
        """Enforce that at least one package exists per picking.

        This is required in order to ensure that the correct dimensional
        weight is applied for the dispatch rates.
        """
        self.ensure_one()
        if self.env.context.get('force_send'):
            return super(StockPicking, self).send_to_shipper()
        if not self.package_ids:
            return self.put_in_pack()
        if self.package_ids.filtered(lambda r: not r.packaging_id):
            wizard = self.env['delivery.package.wizard'].create({
                'picking_id': self.id,
            })
            return wizard.action_show()
        return super(StockPicking, self).send_to_shipper()
