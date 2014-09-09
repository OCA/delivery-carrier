# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Guewen Baconnier
#    Copyright 2014 Camptocamp SA
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
from openerp.tools.translate import _


class picking_dispatch_apply_carrier(orm.TransientModel):
    _name = 'picking.dispatch.apply.carrier'
    _description = 'Picking Dispatch Apply Carrier'

    _columns = {
        'carrier_id': fields.many2one(
            'delivery.carrier',
            string='Carrier',
            required=True),
    }

    def _check_domain(self, cr, uid, ids, picking_ids, context=None):
        """ A domain excluding the dispatches on which we don't allow
        to change the carrier.

        Can be overrided to change the domain.
        """
        return [('state', '!=', 'done'),
                ('id', 'in', picking_ids)]

    def apply(self, cr, uid, ids, context=None):
        if context is None:
            context = {}

        picking_ids = context.get('active_ids')
        if not picking_ids:
            raise orm.except_orm(
                _('Error'),
                _('No selected picking dispatch'))

        assert len(ids) == 1
        this = self.browse(cr, uid, ids[0], context=context)

        dispatch_obj = self.pool['picking.dispatch']
        domain = self._check_domain(cr, uid, ids, picking_ids, context=context)
        dispatch_ids = dispatch_obj.search(cr, uid, domain, context=context)
        dispatch_obj.write(cr, uid, dispatch_ids,
                           {'carrier_id': this.carrier_id.id},
                           context=context)
        dispatch_obj.action_set_options(cr, uid, dispatch_ids, context=context)
        return {'type': 'ir.actions.act_window_close'}
