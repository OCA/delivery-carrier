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
    _inherit = 'stock.picking'

    def _get_carrier_type_selection(self, cr, uid, context=None):
        carrier_obj = self.pool.get('delivery.carrier')
        return carrier_obj._get_carrier_type_selection(cr, uid, context=context)

    _columns = {
        'carrier_id': fields.many2one(
            'delivery.carrier', 'Carrier',
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

    def generate_default_label(self, cr, uid, ids, tracking_ids=None,
                               context=None):
        """ Abstract method

        :param tracking_ids: optional list of ``stock.tracking`` ids
                             only packs in this list will have their label
                             printed (all are generated when None)

        :return: (file_binary, file_type)

        """
        raise orm.except_orm(
                'Error',
                'No label is configured for selected delivery method.')

    def generate_shipping_labels(self, cr, uid, ids, tracking_ids=None,
                                 context=None):
        """Generate a shipping label by default

        This method can be inherited to create specific shipping labels
        a list of label must be return as we can have multiple
        stock.tracking for a single picking representing packs

        :param tracking_ids: optional list of ``stock.tracking`` ids
                             only packs in this list will have their label
                             printed (all are generated when None)

        :return: list of dict containing
           name: name to give to the attachement
           file: file as string
           file_type: string of file type like 'PDF'
           (optional)
           tracking_id: tracking_id if picking lines have tracking_id and
                        if label generator creates shipping label per
                        pack

        """
        default_label = self.generate_default_label(cr, uid, ids,
                                                    tracking_ids=tracking_ids,
                                                    context=None)
        if not tracking_ids:
            return [default_label]
        labels = []
        for tracking_id in tracking_ids:
            pack_label = default_label.copy()
            pack_label['tracking_id'] = tracking_id
            labels.append(pack_label)
        return labels

    def generate_labels(self, cr, uid, ids, tracking_ids=None, context=None):
        """ Generate the labels.

        A list of tracking ids can be given, in that case it will generate
        the labels only of these trackings.

        """
        shipping_label_obj = self.pool.get('shipping.label')

        pickings = self.browse(cr, uid, ids, context=context)

        for pick in pickings:
            shipping_labels = pick.generate_shipping_labels(tracking_ids=tracking_ids)
            for label in shipping_labels:
                # map types with models
                types = {'in': 'stock.picking.in',
                         'out': 'stock.picking.out',
                         'internal': 'stock.picking',
                         }
                res_model = types[pick.type]
                data = {
                    'name': label['name'],
                    'res_id': pick.id,
                    'res_model': res_model,
                    'datas': label['file'].encode('base64'),
                    'file_type': label['file_type'],
                }
                if label.get('tracking_id'):
                    data['tracking_id'] = label['tracking_id']
                context_attachment = context.copy()
                # remove default_type setted for stock_picking
                # as it would try to define default value of attachement
                if 'default_type' in context_attachment:
                    del context_attachment['default_type']
                shipping_label_obj.create(cr, uid, data, context=context_attachment)
        return True

    def action_generate_carrier_label(self, cr, uid, ids, context=None):
        """ Method for the 'Generate Label' button.

        It will generate the labels for all the trackings of the picking.

        """
        return self.generate_labels(cr, uid, ids, context=context)

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

    def _values_with_carrier_options(self, cr, uid, values, context=None):
        values = values.copy()
        carrier_id = values.get('carrier_id')
        option_ids = values.get('option_ids')
        if carrier_id and not option_ids:
            res = self.carrier_id_change(cr, uid, [], carrier_id,
                                         context=context)
            option_ids = res.get('value', {}).get('option_ids')
            if option_ids:
                values.update(option_ids=[(6, 0, option_ids)])
        return values

    def write(self, cr, uid, ids, values, context=None):
        """ Set the default options when the delivery method is changed.

        So we are sure that the options are always in line with the
        current delivery method.

        """
        values = self._values_with_carrier_options(cr, uid, values,
                                                   context=context)
        return super(stock_picking, self).\
            write(cr, uid, ids, values, context=context)

    def create(self, cr, uid, values, context=None):
        """ Trigger carrier_id_change on create

        To ensure options are setted on the basis of carrier_id copied from
        Sale order or defined by default.

        """
        values = self._values_with_carrier_options(cr, uid, values,
                                                   context=context)
        picking_id = super(stock_picking, self
                    ).create(cr, uid, values, context=context)
        return picking_id


class stock_picking_in(orm.Model):
    """ Add what isn't inherited from stock.picking """
    _inherit = 'stock.picking.in'

    def _get_carrier_type_selection(self, cr, uid, context=None):
        carrier_obj = self.pool.get('delivery.carrier')
        return carrier_obj._get_carrier_type_selection(cr, uid, context=context)

    _columns = {
        'carrier_id': fields.many2one(
            'delivery.carrier', 'Carrier',
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

    def generate_labels(self, cr, uid, ids, tracking_ids=None, context=None):
        picking_obj = self.pool.get('stock.picking')
        return picking_obj.generate_labels(cr, uid, ids,
                                           tracking_ids=tracking_ids,
                                           context=context)

    def action_generate_carrier_label(self, cr, uid, ids, context=None):
        picking_obj = self.pool.get('stock.picking')
        return picking_obj.action_generate_carrier_label(
            cr, uid, ids, context=context)

    def carrier_id_change(self, cr, uid, ids, carrier_id, context=None):
        """ Call stock.picking carrier_id_change """
        picking_obj = self.pool.get('stock.picking')
        return picking_obj.carrier_id_change(cr, uid, ids,
                                             carrier_id, context=context)

    def option_ids_change(self, cr, uid, ids,
                          option_ids, carrier_id, context=None):
        """ Call stock.picking option_ids_change """
        picking_obj = self.pool.get('stock.picking')
        return picking_obj.option_ids_change(cr, uid, ids,
                                             option_ids, carrier_id,
                                             context=context)

    def write(self, cr, uid, ids, values, context=None):
        """ Set the default options when the delivery method is changed.

        So we are sure that the options are always in line with the
        current delivery method.

        """
        picking_obj = self.pool['stock.picking']
        values = picking_obj._values_with_carrier_options(cr, uid, values,
                                                          context=context)
        return super(stock_picking_in, self).\
            write(cr, uid, ids, values, context=context)

    def create(self, cr, uid, values, context=None):
        """ Trigger carrier_id_change on create

        To ensure options are setted on the basis of carrier_id copied from
        Sale order or defined by default.

        """
        picking_obj = self.pool['stock.picking']
        values = picking_obj._values_with_carrier_options(cr, uid, values,
                                                          context=context)
        picking_id = super(stock_picking_in, self
                    ).create(cr, uid, values, context=context)
        return picking_id


class stock_picking_out(orm.Model):
    """ Add what isn't inherited from stock.picking """
    _inherit = 'stock.picking.out'

    def _get_carrier_type_selection(self, cr, uid, context=None):
        carrier_obj = self.pool.get('delivery.carrier')
        return carrier_obj._get_carrier_type_selection(cr, uid, context=context)

    _columns = {
        'carrier_id': fields.many2one(
            'delivery.carrier', 'Carrier',
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

    def generate_labels(self, cr, uid, ids, tracking_ids=None, context=None):
        picking_obj = self.pool.get('stock.picking')
        return picking_obj.generate_labels(cr, uid, ids,
                                           tracking_ids=tracking_ids,
                                           context=context)

    def action_generate_carrier_label(self, cr, uid, ids, context=None):
        picking_obj = self.pool.get('stock.picking')
        return picking_obj.action_generate_carrier_label(
            cr, uid, ids, context=context)

    def _get_label_sender_address(self, cr, uid, picking, context=None):
        """ On each carrier label module you need to define
            which is the sender of the parcel.
            The most common case is 'picking.company_id.partner_id'
            which is suitable for each delivery carrier label module.
            But your client might want to customize sender address
            if he has several brands and/or shops in his company.
            In this case he doesn't want his customer to see
            the address of his company in his transport label
            but instead, the address of the partner linked to his shop/brand

            To reach this modularity, call this method to get sender address
            in your delivery_carrier_label_yourcarrier module, then every developer
            can manage specific needs by inherit this method in module like :
            delivery_carrier_label_yourcarrier_yourproject.
        """
        return picking.company_id.partner_id

    def carrier_id_change(self, cr, uid, ids, carrier_id, context=None):
        """ Inherit this method in your module """
        picking_obj = self.pool.get('stock.picking')
        return picking_obj.carrier_id_change(cr, uid, ids, carrier_id, context=context)

    def option_ids_change(self, cr, uid, ids, option_ids, carrier_id, context=None):
        picking_obj = self.pool.get('stock.picking')
        return picking_obj.option_ids_change(cr, uid, ids,
                                             option_ids, carrier_id,
                                             context=context)

    def write(self, cr, uid, ids, values, context=None):
        """ Set the default options when the delivery method is changed.

        So we are sure that the options are always in line with the
        current delivery method.

        """
        picking_obj = self.pool['stock.picking']
        values = picking_obj._values_with_carrier_options(cr, uid, values,
                                                          context=context)
        return super(stock_picking_out, self).\
            write(cr, uid, ids, values, context=context)

    def create(self, cr, uid, values, context=None):
        """ Trigger carrier_id_change on create

        To ensure options are setted on the basis of carrier_id copied from
        Sale order or defined by default.

        """
        picking_obj = self.pool['stock.picking']
        values = picking_obj._values_with_carrier_options(cr, uid, values,
                                                          context=context)
        picking_id = super(stock_picking_out, self
                    ).create(cr, uid, values, context=context)
        return picking_id


class ShippingLabel(orm.Model):
    """ Child class of ir attachment to identify which are labels """
    _inherits = {'ir.attachment': 'attachment_id'}
    _name = 'shipping.label'
    _description = "Shipping Label"

    def _get_file_type_selection(self, cr, uid, context=None):
        """ To inherit to add file type """
        return [('pdf', 'PDF')]

    def __get_file_type_selection(self, cr, uid, context=None):
        file_types = self._get_file_type_selection(cr, uid, context=context)
        file_types = list(set(file_types))
        file_types.sort(key=lambda t: t[0])
        return file_types

    _columns = {
        'file_type': fields.selection(__get_file_type_selection, 'File type'),
        'tracking_id': fields.many2one('stock.tracking', 'Pack'),
    }

    _defaults = {
        'file_type': 'pdf'
    }
