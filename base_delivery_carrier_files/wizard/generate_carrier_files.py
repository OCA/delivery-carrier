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

from openerp.osv import orm, fields
from tools.translate import _


class DeliveryCarrierFileGenerate(orm.TransientModel):

    _name = 'delivery.carrier.file.generate'

    def _get_picking_ids(self, cr, uid, context=None):
        if context is None: context = {}
        res = False
        if (context.get('active_model', False) == 'stock.picking.out' and
            context.get('active_ids', False)):
            res = context['active_ids']
        return res

    _columns = {
        'picking_ids': fields.many2many('stock.picking.out',
                                        string='Delivery Orders'),
    }

    _defaults = {
        'picking_ids': _get_picking_ids,
    }

    def action_generate(self, cr, uid, ids, context=None):
        """
        Call the creation of the delivery carrier files
        """
        context = context or {}
        form = self.browse(cr, uid, ids, context=context)[0]
        if not form.picking_ids:
            raise osv.except_osv(_('Error'), _('No delivery orders selected'))

        picking_obj = self.pool.get('stock.picking.out')
        picking_ids = [picking.id for picking in form.picking_ids]
        picking_obj.generate_carrier_files(cr, uid,
                                           picking_ids,
                                           auto=False,
                                           context=context)

        return {'type': 'ir.actions.act_window_close'}

