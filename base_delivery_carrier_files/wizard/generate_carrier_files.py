# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Guewen Baconnier
#    Copyright 2012 Camptocamp SA
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

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
