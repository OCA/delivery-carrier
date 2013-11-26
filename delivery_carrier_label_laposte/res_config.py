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

from postlogistics.web_service import PostlogisticsWebService


class PostlogisticsConfigSettings(orm.TransientModel):
    _name = 'postlogistics.config.settings'
    _inherit = 'res.config.settings'

    _columns = {
        'company_id': fields.many2one('res.company', 'Company', required=True),
        'wsdl_url': fields.related(
            'company_id', 'postlogistics_wsdl_url',
            string='WSDL URL', type='char'),
        'username': fields.related(
            'company_id', 'postlogistics_username',
            string='Username', type='char'),
        'password': fields.related(
            'company_id', 'postlogistics_password',
            string='Password', type='char'),
        'license_less_1kg': fields.related(
            'company_id', 'postlogistics_license_less_1kg',
            string='License less than 1kg', type='char'),
        'license_more_1kg': fields.related(
            'company_id', 'postlogistics_license_more_1kg',
            string='License more than 1kg', type='char'),
        'license_vinolog': fields.related(
            'company_id', 'postlogistics_license_vinolog',
            string='License VinoLog', type='char'),
        'logo': fields.related(
            'company_id', 'postlogistics_logo',
            string='Company Logo on Post labels', type='binary',
            help="Optional company logo to show on label.\n"
                 "If using an image / logo, please note the following:\n"
                 "– Image width: 47 mm\n"
                 "– Image height: 25 mm\n"
                 "– File size: max. 30 kb\n"
                 "– File format: GIF or PNG\n"
                 "– Colour table: indexed colours, max. 200 colours\n"
                 "– The logo will be printed rotated counter-clockwise by 90°\n"
                 "We recommend using a black and white logo for printing in the\n"
                 "ZPL2 format."
            ),
        'office': fields.related(
            'company_id', 'postlogistics_office',
            string='Domicile Post office', type='char',
            help="Post office which will receive the shipped goods"),
        #'default_postlogistics_logo_layout': fields.related(
            #'company_id', 'default_postlogistics_logo_layout',
            #string='Domicile Post office', type='char',
            #help="Post office which will receive the shipped goods"),
        #'default_postlogistics_output_format': fields.related(
            #'company_id', 'default_postlogistics_logo_layout',
            #string='Domicile Post office', type='char',
            #help="Post office which will receive the shipped goods"),
        #'default_postlogistics_output_format': fields.related(
            #'company_id', 'default_postlogistics_logo_layout',
            #string='Domicile Post office', type='char',
            #help="Post office which will receive the shipped goods"),
        }

    def _default_company(self, cr, uid, context=None):
        user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        return user.company_id.id

    _defaults = {
        'company_id': _default_company,
        }

    def create(self, cr, uid, values, context=None):
        id = super(PostlogisticsConfigSettings, self).create(cr, uid, values, context)
        # Hack: to avoid some nasty bug, related fields are not written upon record creation.
        # Hence we write on those fields here.
        vals = {}
        for fname, field in self._columns.iteritems():
            if isinstance(field, fields.related) and fname in values:
                vals[fname] = values[fname]
        self.write(cr, uid, [id], vals, context)
        return id

    def onchange_company_id(self, cr, uid, ids, company_id, context=None):
        # update related fields
        values = {}
        values['currency_id'] = False
        if company_id:
            company = self.pool.get('res.company').browse(cr, uid, company_id, context=context)
            values = {
                'username': company.postlogistics_username,
                'password': company.postlogistics_password,
                'license_less_1kg': company.postlogistics_license_less_1kg,
                'license_more_1kg': company.postlogistics_license_more_1kg,
                'license_vinolog': company.postlogistics_license_vinolog,
                'logo': company.postlogistics_logo,
                'office': company.postlogistics_office,
            }
        return {'value': values}

    def _get_delivery_instructions(self, cr, uid, ids, web_service,
                                   company, service_code, context=None):
        if context is None:
            context = {}

        lang = context.get('lang', 'en')
        service_code_list = service_code.split(',')
        res = web_service.read_delivery_instructions(company, service_code_list, lang)
        if 'errors' in res:
            errors = '\n'.join(res['errors'])
            error_message = ('Could not retrieve Postlogistics delivery instructions:\n%s'
                             % (errors,))
            raise orm.except_orm('Error', error_message)

        if not res['value']:
            return {}

        if hasattr(res['value'], 'Errors') and res['value'].Errors:
            for error in res['value'].Errors.Error:
                message = '[%s] %s' % (error.Code, error.Message)
            raise orm.except_orm('Error', message)

        delivery_instructions = {}
        for service in res['value'].DeliveryInstructions:
            service_code = service.PRZL
            delivery_instructions[service_code] = {'name': service.Description}

        return delivery_instructions

    def _update_delivery_instructions(self, cr, uid, ids, web_service,
                                      additional_services, context=None):
        if context is None:
            context = {}
        ir_model_data_obj = self.pool.get('ir.model.data')
        carrier_option_obj = self.pool.get('delivery.carrier.template.option')

        postlogistics_partner = ir_model_data_obj.get_object(
            cr, uid, 'delivery_carrier_label_laposte', 'postlogistics', context=context)

        for service_code, data in additional_services.iteritems():

            option_ids = carrier_option_obj.search(cr, uid, [
                ('code', '=', service_code),
                ('postlogistics_type', '=', 'delivery')
                ], context=context)

            if option_ids:
                carrier_option_obj.write(cr, uid, option_ids, data, context=context)
            else:
                data.update(code=service_code,
                            postlogistics_type='delivery',
                            partner_id=postlogistics_partner.id)
                carrier_option_obj.create(cr, uid, data, context=context)

    def _get_additional_services(self, cr, uid, ids, web_service,
                                 company, service_code, context=None):
        if context is None:
            context = {}

        lang = context.get('lang', 'en')
        service_code_list = service_code.split(',')
        res = web_service.read_additional_services(company, service_code_list, lang)
        if 'errors' in res:
            errors = '\n'.join(res['errors'])
            error_message = 'Could not retrieve Postlogistics base services:\n%s' % (errors,)
            raise orm.except_orm('Error', error_message)

        if not res['value']:
            return {}

        if hasattr(res['value'], 'Errors') and res['value'].Errors:
            for error in res['value'].Errors.Error:
                message = '[%s] %s' % (error.Code, error.Message)
            raise orm.except_orm('Error', message)

        additional_services = {}
        for service in res['value'].AdditionalService:
            service_code = service.PRZL
            additional_services[service_code] = {'name': service.Description}

        return additional_services

    def _update_additional_services(self, cr, uid, ids, web_service,
                                    additional_services, context=None):
        if context is None:
            context = {}
        ir_model_data_obj = self.pool.get('ir.model.data')
        carrier_option_obj = self.pool.get('delivery.carrier.template.option')

        postlogistics_partner = ir_model_data_obj.get_object(
            cr, uid, 'delivery_carrier_label_laposte', 'postlogistics', context=context)

        for service_code, data in additional_services.iteritems():

            option_ids = carrier_option_obj.search(cr, uid, [
                ('code', '=', service_code),
                ('postlogistics_type', '=', 'additional')
                ], context=context)

            if option_ids:
                carrier_option_obj.write(cr, uid, option_ids, data, context=context)
            else:
                data.update(code=service_code,
                            postlogistics_type='additional',
                            partner_id=postlogistics_partner.id)
                carrier_option_obj.create(cr, uid, data, context=context)

    def _update_basic_services(self, cr, uid, ids, web_service, company, group_id, context=None):
        """
        Update of basic services
        A basic service can be part only of one service group
        :return: {additional_services: {<service_code>: service_data}
                  delivery_instructions: {<service_code>: service_data}
                  }
        """
        if context is None:
            context = {}
        ir_model_data_obj = self.pool.get('ir.model.data')
        service_group_obj = self.pool.get('postlogistics.service.group')
        carrier_option_obj = self.pool.get('delivery.carrier.template.option')

        postlogistics_partner = ir_model_data_obj.get_object(
            cr, uid, 'delivery_carrier_label_laposte', 'postlogistics', context=context)
        lang = context.get('lang', 'en')

        group = service_group_obj.browse(cr, uid, group_id, context=context)

        res = web_service.read_basic_services(company, group.group_extid, lang)
        if 'errors' in res:
            errors = '\n'.join(res['errors'])
            error_message = 'Could not retrieve Postlogistics base services:\n%s' % (errors,)
            raise orm.except_orm('Error', error_message)

        additional_services = {}
        delivery_instructions = {}
        # Create or update basic service
        for service in res['value'].BasicService:
            service_code = ','.join(service.PRZL)
            option_ids = carrier_option_obj.search(cr, uid, [
                ('code', '=', service_code),
                ('postlogistics_service_group_id', '=', group_id),
                ('postlogistics_type', '=', 'basic')
                ], context=context)
            data = {'name': service.Description}
            if option_ids:
                carrier_option_obj.write(cr, uid, option_ids, data, context=context)
                option_id = option_ids[0]
            else:
                data.update(code=service_code,
                            postlogistics_service_group_id=group_id,
                            partner_id=postlogistics_partner.id,
                            postlogistics_type='basic')
                option_id = carrier_option_obj.create(cr, uid, data, context=context)

            # Get related services
            allowed_services = self._get_additional_services(
                cr, uid, ids, web_service, company, service_code, context=context)
            for key, value in additional_services.iteritems():
                if key in allowed_services:
                    additional_services[key]['postlogistics_basic_service_ids'][0][2].append(option_id)
                    del allowed_services[key]
            for key, value in allowed_services.iteritems():
                additional_services[key] = value
                additional_services[key]['postlogistics_basic_service_ids'] = [(6, 0, [option_id])]

            allowed_services = self._get_delivery_instructions(
                cr, uid, ids, web_service, company, service_code, context=context)
            for key, value in delivery_instructions.iteritems():
                if key in allowed_services:
                    delivery_instructions[key]['postlogistics_basic_service_ids'][0][2].append(option_id)
                    del allowed_services[key]
            for key, value in allowed_services.iteritems():
                delivery_instructions[key] = value
                delivery_instructions[key]['postlogistics_basic_service_ids'] = [(6, 0, [option_id])]

        return {'additional_services': additional_services,
                'delivery_instructions': delivery_instructions}

    def _update_service_groups(self, cr, uid, ids, web_service, company, context=None):
        """
        Also updates additional services and delivery instructions as they are shared between groups
        """
        if context is None:
            context = {}
        service_group_obj = self.pool.get('postlogistics.service.group')

        lang = context.get('lang', 'en')

        res = web_service.read_service_groups(company, lang)
        if 'errors' in res:
            errors = '\n'.join(res['errors'])
            error_message = 'Could not retrieve Postlogistics group services:\n%s' % (errors,)
            raise orm.except_orm('Error', error_message)

        additional_services = {}
        delivery_instructions = {}

        # Create or update groups
        for group in res['value'].ServiceGroup:
            group_extid = group.ServiceGroupID
            group_ids = service_group_obj.search(
                cr, uid, [('group_extid', '=', group_extid)], context=context)
            data = {'name': group.Description}
            if group_ids:
                service_group_obj.write(cr, uid, group_ids, data, context=context)
                group_id = group_ids[0]
            else:
                data['group_extid'] = group_extid
                group_id = service_group_obj.create(cr, uid, data, context=context)

            # Get related services for all basic services of this group
            res = self._update_basic_services(cr, uid, ids, web_service,
                                              company, group_id, context=context)

            allowed_services = res.get('additional_services', {})
            for key, value in additional_services.iteritems():
                if key in allowed_services:
                    option_ids = allowed_services[key]['postlogistics_basic_service_ids'][0][2]
                    additional_services[key]['postlogistics_basic_service_ids'][0][2].extend(option_ids)
                    del allowed_services[key]
            additional_services.update(allowed_services)

            allowed_services = res.get('delivery_instructions', {})
            for key, value in delivery_instructions.iteritems():
                if key in allowed_services:
                    option_ids = allowed_services[key]['postlogistics_basic_service_ids'][0][2]
                    delivery_instructions[key]['postlogistics_basic_service_ids'][0][2].extend(option_ids)
                    del allowed_services[key]
            delivery_instructions.update(allowed_services)

        # Update related services
        self._update_additional_services(cr, uid, ids, web_service,
                                         additional_services, context=context)
        self._update_delivery_instructions(cr, uid, ids, web_service,
                                           delivery_instructions, context=context)

    def update_postlogistics_options(self, cr, uid, ids, context=None):
        """
        This action will update all postlogistics option by importing services
        from PostLogistics WebService API

        The object we create are 'delivey.carrier.template.option'
        """
        if context is None:
            context = {}
        user_obj = self.pool.get('res.users')

        company = user_obj.browse(cr, uid, uid, context=context).company_id

        web_service = PostlogisticsWebService(company)

        # make sure we create source text in en_US
        ctx = context.copy()
        ctx['lang'] = 'en_US'
        self._update_service_groups(cr, uid, ids, web_service, company, context=ctx)

        language_obj = self.pool.get('res.lang')
        language_ids = language_obj.search(cr, uid, [], context=context)

        languages = language_obj.browse(cr, uid, language_ids, context=context)

        # handle translations
        # we call the same methode with a different language context
        for lang_br in languages:
            lang = lang_br.code
            ctx = context.copy()
            ctx['lang'] = lang_br.code
            postlogistics_lang = web_service._get_language(lang)
            # add translations only for languages that exists on postlogistics
            # english source will be kept for other languages
            if postlogistics_lang == 'en':
                continue
            self._update_service_groups(cr, uid, ids, web_service, company, context=ctx)
        return True
