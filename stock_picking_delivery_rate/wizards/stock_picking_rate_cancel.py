# -*- coding: utf-8 -*-
# Copyright 2017 LasLabs Inc.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import api, models


class StockPickingRateCancel(models.TransientModel):
    """Cancel a set of stock rates."""

    _name = "stock.picking.rate.cancel"
    _inherit = 'stock.picking.rate.wizard.abstract'
    _description = 'Stock Picking Dispatch Rate Cancel'

    @api.multi
    def action_cancel(self):
        """Cancel rate quotes."""

        self.ensure_one()

        search_for = ['stock.picking.rate,%d' % r.id for r in self.rate_ids]
        purchase_orders = self.env['purchase.order'].search([
            ('order_line.reference', 'in', search_for),
        ])
        purchase_orders.button_cancel()

        return self.action_show_purchases(purchase_orders)
