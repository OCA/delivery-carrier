# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Yannick Vaucher
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


class PostlogisticsServiceGroup(orm.Model):
    _name = 'postlogistics.service.group'
    _description = 'PostLogistics Service Group'

    _columns = {
        'name': fields.char('Description', translate=True, required=True),
        'group_extid': fields.integer('Group ID', required=True),
    }

    _sql_constraints = [
        ('group_extid_uniq', 'unique(group_extid)',
         "A service group ID must be unique.")
    ]


POSTLOGISTIC_TYPES = [
    ('label_layout', 'Label Layout'),
    ('output_format', 'Output Format'),
    ('resolution', 'Output Resolution'),
    ('basic', 'Basic Service'),
    ('additional', 'Additional Service'),
    ('delivery', 'Delivery Instructions')
]


class DeliveryCarrierTemplateOption(orm.Model):
    """ Set name translatable and add service group """
    _inherit = 'delivery.carrier.template.option'

    _columns = {
        'name': fields.char('Name', size=64, translate=True),
        'postlogistics_service_group_id': fields.many2one(
            'postlogistics.service.group',
            string='PostLogistics Service Group'),
        'postlogistics_type': fields.selection(
            POSTLOGISTIC_TYPES,
            string="PostLogistics option type"),
        # relation tables to manage compatiblity between basic services
        # and other services
        'postlogistics_basic_service_ids': fields.many2many(
            'delivery.carrier.template.option',
            'postlogistics_compatibility_service_rel',
            'service_id', 'basic_service_id',
            string="Basic Services",
            domain=[('postlogistics_type', '=', 'basic')],
            help="List of basic service for which this service is compatible"),
        'postlogistics_additonial_service_ids': fields.many2many(
            'delivery.carrier.template.option',
            'postlogistics_compatibility_service_rel',
            'basic_service_id', 'service_id',
            string="Compatible Additional Services",
            domain=[('postlogistics_type', '=', 'additional')]),
        'postlogistics_delivery_instruction_ids': fields.many2many(
            'delivery.carrier.template.option',
            'postlogistics_compatibility_service_rel',
            'basic_service_id', 'service_id',
            string="Compatible Delivery Instructions",
            domain=[('postlogistics_type', '=', 'delivery')]),
    }

    _defaults = {
        'postlogistics_type': False,
    }


class DeliveryCarrierOption(orm.Model):
    """ Set name translatable and add service group """
    _inherit = 'delivery.carrier.option'

    _columns = {
        'name': fields.char('Name', size=64, translate=True),
        # to repeat carrier allowed option ids to filter domain set by
        # default from view
        'allowed_option_ids': fields.related(
            'carrier_id', 'allowed_option_ids', type='many2many',
            relation='delivery.carrier.template.option',
            string='Allowed and compatible options',
            readonly=True),
    }


class DeliveryCarrier(orm.Model):
    """ Add service group """
    _inherit = 'delivery.carrier'

    def _get_carrier_type_selection(self, cr, uid, context=None):
        """ To inherit to add carrier type """
        res = super(DeliveryCarrier, self)._get_carrier_type_selection(cr, uid, context=context)
        res.append(('postlogistics', 'Postlogistics'))
        return res

    def _get_basic_service_id(self, cr, uid, ids, field_names, arg, context=None):
        """ Search in all options for the postlogistic basic service if set """
        res = dict.fromkeys(ids, False)
        ir_model_data_obj = self.pool.get('ir.model.data')

        xmlid = 'delivery_carrier_label_laposte', 'postlogistics'
        postlogistics_partner = ir_model_data_obj.get_object(
            cr, uid, *xmlid, context=context)

        for carrier in self.browse(cr, uid, ids, context=context):
            if not carrier.partner_id.id == postlogistics_partner.id:
                continue

            option_ids = [opt.tmpl_option_id.id for opt
                          in carrier.available_option_ids
                          if opt.postlogistics_type == 'basic']
            if not option_ids:
                continue
            res[carrier.id] = option_ids[0]
        return res

    def _get_allowed_option_ids(self, cr, uid, ids, field_names, arg, context=None):
        """ Return a list of possible options

        A domain would be too complicated.

        We do this to ensure the user first select a basic service. And
        then he adds additional services.

        :return: {carrier_id: [ids]}

        """
        res = dict.fromkeys(ids, [])
        option_template_obj = self.pool.get('delivery.carrier.template.option')
        ir_model_data_obj = self.pool.get('ir.model.data')

        xmlid = 'delivery_carrier_label_laposte', 'postlogistics'
        postlogistics_partner = ir_model_data_obj.get_object(
            cr, uid, *xmlid, context=context)

        for carrier in self.browse(cr, uid, ids, context=context):
            allowed_ids = []
            if not carrier.partner_id.id == postlogistics_partner.id:
                continue
            service_group_id = carrier.postlogistics_service_group_id.id
            if service_group_id:
                # if there are no basic option set. Show basic options
                basic_service_id = carrier.postlogistics_basic_service_id.id
                if not basic_service_id:
                    service_ids = option_template_obj.search(
                        cr, uid,
                        [('postlogistics_service_group_id' ,'=', service_group_id)],
                        context=context)
                else:
                    service_ids = option_template_obj.search(
                        cr, uid,
                        [('postlogistics_basic_service_ids' ,'in', basic_service_id)],
                        context=context)
                allowed_ids.extend(service_ids)

            # Allows to set multiple optional single option in order to
            # let the user select them
            single_option_types = ['label_layout', 'output_format', 'resolution']
            selected_single_options = [opt.tmpl_option_id.postlogistics_type
                                       for opt in carrier.available_option_ids
                                       if opt.postlogistics_type in single_option_types
                                       and opt.state in ['mandatory']]
            if selected_single_options != single_option_types:
                service_ids = option_template_obj.search(
                    cr, uid,
                    [('postlogistics_type', 'in', single_option_types),
                     ('postlogistics_type', 'not in', selected_single_options)],
                    context=context)
                allowed_ids.extend(service_ids)
            res[carrier.id] = allowed_ids
        return res

    _columns = {
        'type': fields.selection(
            _get_carrier_type_selection, 'Type',
            help="Carrier type (combines several delivery methods)"),
        'postlogistics_service_group_id': fields.many2one(
            'postlogistics.service.group',
            string='PostLogistics Service Group',
            help="Service group defines the available options for "
                 "this delivery method."),
        'postlogistics_basic_service_id': fields.function(
            _get_basic_service_id, type='many2one',
            relation='delivery.carrier.template.option',
            string='PostLogistics Service Group',
            help="Basic Service defines the available "
                 "additional options for this delivery method",
            readonly=True),
        'allowed_option_ids': fields.function(
            _get_allowed_option_ids, type="many2many",
            relation='delivery.carrier.template.option',
            string='Allowed options',
            help="Compute allowed options according to selected options."),
    }
