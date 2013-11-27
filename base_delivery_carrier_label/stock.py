# -*- coding: utf-8 -*-
##############################################################################
#
#    Authors: David BEAL <david.beal@akretion.com>
#             Sébastien BEAU <sebastien.beau@akretion.com>
#    Copyright (C) 2012-TODAY Akretion <http://www.akretion.com>.
#    Author: Yannick Vaucher <yannick.vaucher@camptocamp.com>
#    Copyright 2013 Camptocamp SA
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


class stock_picking(orm.Model):
    """ Define m2m field due to inheritance to have it in stock.picking.out """
    _inherit = 'stock.picking'

    _columns = {
        'option_ids': fields.many2many('delivery.carrier.option',
                                       string='Options'),
    }


class stock_picking_out(orm.Model):
    _inherit = 'stock.picking.out'

    def _get_carrier_type_selection(self, cr, uid, context=None):
        carrier_obj = self.pool.get('delivery.carrier')
        return carrier_obj._get_carrier_type_selection(cr, uid, context=context)

    _columns = {
        'carrier_id': fields.many2one(
            'delivery.carrier', 'Carrier',
            states={'done': [('readonly', True)]}),
        'carrier_tracking_ref': fields.char(
            'Carrier Tracking Ref',
            size=32,
            states={'done': [('readonly', True)]}),
        'carrier_type': fields.related(
            'carrier_id', 'type',
            string='Carrier type',
            readonly=True,
            type='selection',
            selection=_get_carrier_type_selection,
            help="Carrier type ('group')"),
        'carrier_code': fields.related(
            'carrier_id', 'code',
            string='Delivery Method Code',
            readonly=True,
            type='char',
            help="Delivery Method Code (from carrier)"),
        'option_ids': fields.many2many('delivery.carrier.option',
                                       string='Options'),
        }

    def generate_default_label(self, cr, uid, ids, context=None):
        """ Abstract method """
        return NotImplementedError

    def generate_single_label(self, cr, uid, ids, context=None):
        """ Generate a the single label by default """
        return self.generate_default_label(cr, uid, ids, context=None)

    def action_generate_carrier_label(self, cr, uid, ids, context=None):
        shipping_label_obj = self.pool.get('shipping.label')

        pickings = self.browse(cr, uid, ids, context=context)

        pdf_list = []
        for pick in pickings:
            pdf = pick.generate_single_label()
            pdf_list.append(pdf)
            data = {
                'name': pick.name,
                'res_id': pick.id,
                'res_model': 'stock.picking.out',
                'datas': pdf.encode('base64'),
                }
            context_attachment = context.copy()
            # remove default_type setted for stock_picking
            # as it would try to define default value of attachement
            if 'default_type' in context_attachment:
                del context_attachment['default_type']
            shipping_label_obj.create(cr, uid, data, context=context_attachment)
        return True

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


class ShippingLabel(orm.Model):
    """ Child class of ir attachment to identify which are labels """
    _inherits = {'ir.attachment': 'attachment_id'}
    _name = "shipping.label"
    _description = "Shipping Label"
