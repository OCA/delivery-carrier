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


class stock_picking(osv.osv):
    _inherit = 'stock.picking'

    _columns = {
        'carrier_file_generated': fields.boolean('Carrier File Generated', readonly=True,
                              help="The file for the delivery carrier has been generated."),
    }

    def generate_carrier_files(self, cr, uid, ids, auto=True, context=None):
        """
        Generates all the files for a list of pickings according to
        their configuration carrier file.
        Does nothing on pickings without carrier or without
        carrier file configuration.
        Generate files only for outgoing pickings.

        :param list ids: list of ids of pickings for which we need a file
        :param auto: specify if we call the method from an automatic action
                     (on process on picking as instance)
                     or called manually from the wizard. When auto is True,
                     only the carrier files set as "auto_export"
                     are exported
        :return: True if successful
        """
        carrier_file_obj = self.pool.get('delivery.carrier.file')
        carrier_file_ids = {}
        for picking in self.browse(cr, uid, ids, context):
            if picking.type != 'out':
                continue
            if picking.carrier_file_generated:
                continue
            if not picking.carrier_id or not picking.carrier_id.carrier_file_id:
                continue
            if auto and not picking.carrier_id.carrier_file_id.auto_export:
                continue
            p_carrier_file_id = picking.carrier_id.carrier_file_id.id
            carrier_file_ids.setdefault(p_carrier_file_id, []).append(picking.id)

        for carrier_file_id, carrier_picking_ids in carrier_file_ids.iteritems():
            carrier_file_obj.generate_files(cr, uid, carrier_file_id,
                                            carrier_picking_ids,
                                            context=context)
        return True

    def action_done(self, cr, uid, ids, context=None):
        result = super(stock_picking, self).action_done(cr, uid, ids, context=context)
        self.generate_carrier_files(cr, uid, ids, auto=True, context=context)
        return result

    def copy(self, cr, uid, id, default=None, context=None):
        if default is None:
            default = {}
        default.update({'carrier_file_generated': False})
        return super(stock_picking, self).copy(cr, uid, id, default, context=context)

stock_picking()
