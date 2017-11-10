# -*- coding: utf-8 -*-
# Copyright 2017 LasLabs Inc.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import api, fields, models


class StockPicking(models.Model):

    _inherit = 'stock.picking'

    dispatch_rate_ids = fields.One2many(
        string='Dispatch Rates',
        comodel_name='stock.picking.rate',
        inverse_name='picking_id',
    )

    @api.multi
    def action_compute_rates(self, clear_old=True):
        """Call this to compute rates for a picking.

        Args:
            clear_old (bool): Delete the old rates.
        """
        for record in self:
            rates = [(0, 0, val) for val in record._compute_rates()]
            if clear_old:
                record.dispatch_rate_ids.unlink()
            record.dispatch_rate_ids = rates

    @api.multi
    def _compute_rates(self):
        """This should be inherited by connector modules to add rates.

        Returns:
            list of dicts: List of dictionaries containing the values for the
                rates.
        """
        self.ensure_one()
        return []
