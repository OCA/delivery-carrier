# -*- coding: utf-8 -*-
# Copyright 2012 Camptocamp SA
# Author: Guewen Baconnier
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, exceptions, api
from openerp.tools.translate import _


class DeliveryCarrierFileGenerate(models.TransientModel):

    _name = 'delivery.carrier.file.generate'

    @api.model
    def _get_pickings(self):
        context = self.env.context
        if (context.get('active_model') == 'stock.picking' and
                context.get('active_ids')):
            return self.env["stock.picking"].browse(
                context["active_ids"])

    @api.multi
    def action_generate(self):
        """
        Call the creation of the delivery carrier files
        """
        if not self.pickings:
            raise exceptions.Warning(_('No delivery orders selected'))
        self.pickings.generate_carrier_files(
            auto=False, recreate=self.recreate)
        return {'type': 'ir.actions.act_window_close'}

    pickings = fields.Many2many('stock.picking',
                                string='Delivery Orders',
                                default=_get_pickings,
                                oldname='picking_ids')
    recreate = fields.Boolean(
        'Recreate files',
        help=("If this option is used, new files will be generated "
              "for selected picking even if they already had one.\n"
              "By default, delivery orders with existing file will be "
              "skipped."))
