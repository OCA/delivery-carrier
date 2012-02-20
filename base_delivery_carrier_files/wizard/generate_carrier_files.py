# -*- coding: utf-8 -*-
##############################################################################
#
#   Copyright (c) 2012 Camptocamp SA (http://www.camptocamp.com)
#   @author Guewen Baconnier
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################

from osv import osv, fields
from tools.translate import _


class DeliveryCarrierFileGenerate(osv.osv_memory):

    _name = 'delivery.carrier.file.generate'

    def _get_picking_ids(self, cr, uid, context=None):
        if context is None: context = {}
        res = False
        if (context.get('active_model', False) == 'stock.picking' and
            context.get('active_ids', False)):
            res = context['active_ids']
        return res

    _columns = {
        'picking_ids': fields.many2many('stock.picking',
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

        picking_obj = self.pool.get('stock.picking')
        picking_ids = [picking.id for picking in form.picking_ids]
        picking_obj.generate_carrier_files(cr, uid,
                                           picking_ids,
                                           auto=False,
                                           context=context)

        return {'type': 'ir.actions.act_window_close'}

DeliveryCarrierFileGenerate()
