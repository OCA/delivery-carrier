# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Sébastien BEAU <sebastien.beau@akretion.com>
#    Copyright (C) 2012-TODAY Akretion <http://www.akretion.com>.
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
from openerp.osv.orm import Model
from openerp.osv import fields
from openerp.tools.translate import _


class PickingDispatch(Model):
    """ Add carrier and carrier options on dispatch

    to be able to massively set those options on related picking.

    """
    _inherit = "picking.dispatch"

    _columns = {
        'carrier_id': fields.many2one(
            'delivery.carrier', 'Carrier',
            states={'done': [('readonly', True)]}),
        'option_ids': fields.many2many(
            'delivery.carrier.option',
            string='Options'),
        }

    def action_set_options(self, cr, uid, ids, context=None):
        """ Apply options to picking of the dispatch

        This will replace all carrier options in picking 

        """
        picking_obj = self.pool.get('stock.picking')
        for dispatch in self.browse(cr, uid, ids, context=context):
            picking_ids = [p.id for p in dispatch.related_picking_ids]

            option_ids = [o.id for o in dispatch.option_ids]
            options_datas = {
                'carrier_id': dispatch.carrier_id.id,
                'option_ids': [(6, 0, option_ids)],
                }
            picking_obj.write(cr, uid, picking_ids,
                              options_datas, context=context)

    def carrier_id_change(self, cr, uid, ids, carrier_id, context=None):
        """ Inherit this method in your module """
        carrier_obj = self.pool.get('delivery.carrier')
        res = {}
        if carrier_id:
            carrier = carrier_obj.browse(cr, uid, carrier_id, context=context)
            # This can look useless as the field carrier_code and
            # carrier_type are related field. But it's needed to fill
            # this field for using this fields in the view. Indeed the
            # module that depend of delivery base can hide some field
            # depending of the type or the code

            default_option_ids = []
            available_option_ids = []
            for available_option in carrier.available_option_ids:
                available_option_ids.append(available_option.id)
                if available_option.state in ['default_option', 'mandatory']:
                    default_option_ids.append(available_option.id)
            res = {
                'value': {'carrier_type': carrier.type,
                          'carrier_code': carrier.code,
                          'option_ids': default_option_ids,
                          },
                'domain': {'option_ids': [('id', 'in', available_option_ids)],
                           },
            }
        return res

    def option_ids_change(self, cr, uid, ids, option_ids, carrier_id, context=None):
        carrier_obj = self.pool.get('delivery.carrier')
        res = {}
        if not carrier_id:
            return res
        carrier = carrier_obj.browse(cr, uid, carrier_id, context=context)
        for available_option in carrier.available_option_ids:
            if (available_option.state == 'mandatory'
                    and not available_option.id in option_ids[0][2]):
                res['warning'] = {
                    'title': _('User Error !'),
                    'message':  _("You can not remove a mandatory option."
                                  "\nOptions are reset to default.")
                }
                default_value = self.carrier_id_change(cr, uid, ids,
                                                       carrier_id,
                                                       context=context)
                res.update(default_value)
        return res
