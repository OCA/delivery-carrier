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
import logging

from openerp.osv import orm, fields
from openerp.tools.translate import _

from .postlogistics.web_service import PostlogisticsWebService

_logger = logging.getLogger(__name__)


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
        'license_ids': fields.related(
            'company_id', 'postlogistics_license_ids',
            string='Frankling Licenses',
            type='one2many',
            relation='postlogistics.license'),
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
                 "– The logo will be printed rotated counter-clockwise by 90°"
                 "\n"
                 "We recommend using a black and white logo for printing in "
                 " the ZPL2 format."
        ),
        'office': fields.related(
            'company_id', 'postlogistics_office',
            string='Domicile Post office', type='char',
            help="Post office which will receive the shipped goods"),

        'default_label_layout': fields.related(
            'company_id', 'postlogistics_default_label_layout',
            string='Default label layout', type='many2one',
            relation='delivery.carrier.template.option',
            domain=[('postlogistics_type', '=', 'label_layout')]),
        'default_output_format': fields.related(
            'company_id', 'postlogistics_default_output_format',
            string='Default output format', type='many2one',
            relation='delivery.carrier.template.option',
            domain=[('postlogistics_type', '=', 'output_format')]),
        'default_resolution': fields.related(
            'company_id', 'postlogistics_default_resolution',
            string='Default resolution', type='many2one',
            relation='delivery.carrier.template.option',
            domain=[('postlogistics_type', '=', 'resolution')]),
    }

    def _default_company(self, cr, uid, context=None):
        user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        return user.company_id.id

    _defaults = {
        'company_id': _default_company,
    }

    def create(self, cr, uid, values, context=None):
        id = super(PostlogisticsConfigSettings, self
                   ).create(cr, uid, values, context=context)
        # Hack: to avoid some nasty bug, related fields are not written
        # upon record creation.  Hence we write on those fields here.
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
        if not company_id:
            return {'value': values}
        company = self.pool.get('res.company'
                                ).browse(cr, uid, company_id, context=context)

        license_ids = [l.id for l in company.postlogistics_license_ids]
        label_layout = company.postlogistics_default_label_layout.id or False
        output_format = company.postlogistics_default_output_format.id or False
        resolution = company.postlogistics_default_resolution.id or False
        values = {
            'username': company.postlogistics_username,
            'password': company.postlogistics_password,
            'license_ids': license_ids,
            'logo': company.postlogistics_logo,
            'office': company.postlogistics_office,
            'default_label_layout': label_layout,
            'default_output_format': output_format,
            'default_resolution': resolution,
        }
        return {'value': values}

    def _get_delivery_instructions(self, cr, uid, ids, web_service,
                                   company, service_code, context=None):
        if context is None:
            context = {}

        lang = context.get('lang', 'en')
        service_code_list = service_code.split(',')
        res = web_service.read_delivery_instructions(
            company, service_code_list, lang)
        if 'errors' in res:
            errors = '\n'.join(res['errors'])
            error_message = (_('Could not retrieve Postlogistics delivery'
                               'instructions:\n%s') % errors)
            raise orm.except_orm(_('Error'), error_message)

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

        xmlid = 'delivery_carrier_label_postlogistics', 'postlogistics'
        postlogistics_partner = ir_model_data_obj.get_object(
            cr, uid, *xmlid, context=context)

        for service_code, data in additional_services.iteritems():

            option_ids = carrier_option_obj.search(
                cr, uid,
                [('code', '=', service_code),
                 ('postlogistics_type', '=', 'delivery')
                 ],
                context=context)

            if option_ids:
                carrier_option_obj.write(cr, uid, option_ids, data,
                                         context=context)
            else:
                data.update(code=service_code,
                            postlogistics_type='delivery',
                            partner_id=postlogistics_partner.id)
                carrier_option_obj.create(cr, uid, data, context=context)
        lang = context.get('lang', 'en')
        _logger.info("Updated delivery instrutions. [%s]" % (lang))

    def _get_additional_services(self, cr, uid, ids, web_service,
                                 company, service_code, context=None):
        if context is None:
            context = {}

        lang = context.get('lang', 'en')
        service_code_list = service_code.split(',')
        res = web_service.read_additional_services(company, service_code_list,
                                                   lang)
        if 'errors' in res:
            errors = '\n'.join(res['errors'])
            error_message = (_('Could not retrieve Postlogistics base '
                               'services:\n%s') % errors)
            raise orm.except_orm(_('Error'), error_message)

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
            cr, uid, 'delivery_carrier_label_postlogistics', 'postlogistics',
            context=context)

        for service_code, data in additional_services.iteritems():

            option_ids = carrier_option_obj.search(
                cr, uid, [
                    ('code', '=', service_code),
                    ('postlogistics_type', '=', 'additional')
                ], context=context)

            if option_ids:
                carrier_option_obj.write(cr, uid, option_ids, data,
                                         context=context)
            else:
                data.update(code=service_code,
                            postlogistics_type='additional',
                            partner_id=postlogistics_partner.id)
                carrier_option_obj.create(cr, uid, data, context=context)
        lang = context.get('lang', 'en')
        _logger.info("Updated additional services [%s]" % (lang))

    def _update_basic_services(self, cr, uid, ids, web_service, company,
                               group_id, context=None):
        """ Update of basic services

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

        xmlid = 'delivery_carrier_label_postlogistics', 'postlogistics'
        postlogistics_partner = ir_model_data_obj.get_object(
            cr, uid, *xmlid, context=context)
        lang = context.get('lang', 'en')

        group = service_group_obj.browse(cr, uid, group_id, context=context)

        res = web_service.read_basic_services(company, group.group_extid, lang)
        if 'errors' in res:
            errors = '\n'.join(res['errors'])
            error_message = (_('Could not retrieve Postlogistics base '
                               'services:\n%s') % errors)
            raise orm.except_orm(_('Error'), error_message)

        additional_services = {}
        delivery_instructions = {}
        # Create or update basic service
        for service in res['value'].BasicService:
            service_code = ','.join(service.PRZL)
            option_ids = carrier_option_obj.search(
                cr, uid, [
                    ('code', '=', service_code),
                    ('postlogistics_service_group_id', '=', group_id),
                    ('postlogistics_type', '=', 'basic')
                ], context=context)
            data = {'name': service.Description}
            if option_ids:
                carrier_option_obj.write(cr, uid, option_ids, data,
                                         context=context)
                option_id = option_ids[0]
            else:
                data.update(code=service_code,
                            postlogistics_service_group_id=group_id,
                            partner_id=postlogistics_partner.id,
                            postlogistics_type='basic')
                option_id = carrier_option_obj.create(cr, uid, data,
                                                      context=context)

            # Get related services
            allowed_services = self._get_additional_services(
                cr, uid, ids, web_service, company, service_code,
                context=context)
            for key, value in additional_services.iteritems():
                if key in allowed_services:
                    (additional_services[key]
                                        ['postlogistics_basic_service_ids']
                                        [0]
                                        [2]).append(option_id)
                    del allowed_services[key]
            for key, value in allowed_services.iteritems():
                value['postlogistics_basic_service_ids'] = [
                    (6, 0, [option_id])]
                additional_services[key] = value

            allowed_services = self._get_delivery_instructions(
                cr, uid, ids, web_service, company, service_code,
                context=context)
            for key, value in delivery_instructions.iteritems():
                if key in allowed_services:
                    (delivery_instructions[key]
                                          ['postlogistics_basic_service_ids']
                                          [0]
                                          [2]).append(option_id)
                    del allowed_services[key]
            for key, value in allowed_services.iteritems():
                value['postlogistics_basic_service_ids'] = [
                    (6, 0, [option_id])]
                delivery_instructions[key] = value

        _logger.info("Updated '%s' basic service [%s]." % (group.name, lang))
        return {'additional_services': additional_services,
                'delivery_instructions': delivery_instructions}

    def _update_service_groups(self, cr, uid, ids, web_service, company,
                               context=None):
        """ Also updates additional services and delivery instructions
        as they are shared between groups

        """
        if context is None:
            context = {}
        service_group_obj = self.pool.get('postlogistics.service.group')

        lang = context.get('lang', 'en')

        res = web_service.read_service_groups(company, lang)
        if 'errors' in res:
            errors = '\n'.join(res['errors'])
            error_message = (_('Could not retrieve Postlogistics group '
                               'services:\n%s') % errors)
            raise orm.except_orm(_('Error'), error_message)

        additional_services = {}
        delivery_instructions = {}

        # Create or update groups
        for group in res['value'].ServiceGroup:
            group_extid = group.ServiceGroupID
            group_ids = service_group_obj.search(
                cr, uid, [('group_extid', '=', group_extid)], context=context)
            data = {'name': group.Description}
            if group_ids:
                service_group_obj.write(cr, uid, group_ids, data,
                                        context=context)
                group_id = group_ids[0]
            else:
                data['group_extid'] = group_extid
                group_id = service_group_obj.create(cr, uid, data,
                                                    context=context)

            # Get related services for all basic services of this group
            res = self._update_basic_services(cr, uid, ids, web_service,
                                              company, group_id,
                                              context=context)

            allowed_services = res.get('additional_services', {})
            for key, value in additional_services.iteritems():
                if key in allowed_services:
                    a = allowed_services[key]
                    option_ids = a['postlogistics_basic_service_ids'][0][2]
                    (additional_services[key]
                                        ['postlogistics_basic_service_ids']
                                        [0]
                                        [2]).extend(option_ids)
                    del allowed_services[key]
            additional_services.update(allowed_services)

            allowed_services = res.get('delivery_instructions', {})
            for key, value in delivery_instructions.iteritems():
                if key in allowed_services:
                    a = allowed_services[key]
                    option_ids = a['postlogistics_basic_service_ids'][0][2]
                    (delivery_instructions[key]
                                          ['postlogistics_basic_service_ids']
                                          [0]
                                          [2]).extend(option_ids)
                    del allowed_services[key]
            delivery_instructions.update(allowed_services)

        # Update related services
        self._update_additional_services(cr, uid, ids, web_service,
                                         additional_services, context=context)
        self._update_delivery_instructions(cr, uid, ids, web_service,
                                           delivery_instructions,
                                           context=context)

    def update_postlogistics_options(self, cr, uid, ids, context=None):
        """ This action will update all postlogistics option by
        importing services from PostLogistics WebService API

        The object we create are 'delivey.carrier.template.option'

        """
        if context is None:
            context = {}
        for config in self.browse(cr, uid, ids, context=context):
            company = config.company_id
            web_service = PostlogisticsWebService(company)

            # make sure we create source text in en_US
            ctx = context.copy()
            ctx['lang'] = 'en_US'
            self._update_service_groups(cr, uid, ids, web_service, company,
                                        context=ctx)

            language_obj = self.pool.get('res.lang')
            language_ids = language_obj.search(cr, uid, [], context=context)

            languages = language_obj.browse(cr, uid, language_ids,
                                            context=context)

            # handle translations
            # we call the same methode with a different language context
            for lang_br in languages:
                lang = lang_br.code
                ctx = context.copy()
                ctx['lang'] = lang_br.code
                postlogistics_lang = web_service._get_language(lang)
                # add translations only for languages that exists on
                # postlogistics english source will be kept for other languages
                if postlogistics_lang == 'en':
                    continue
                self._update_service_groups(cr, uid, ids, web_service, company,
                                            context=ctx)
        return True

    def _get_allowed_service_group_codes(self, web_service, company,
                                         license, context=None):
        """ Get a list of allowed service group codes"""
        if context is None:
            context = {}

        lang = context.get('lang', 'en')
        res = web_service.read_allowed_services_by_franking_license(
            license.number, company, lang)
        if 'errors' in res:
            errors = '\n'.join(res['errors'])
            error_message = (_('Could not retrieve allowed Postlogistics '
                               'service groups for the %s licence:\n%s')
                             % (license.name, errors))
            raise orm.except_orm(_('Error'), error_message)

        if not res['value']:
            return []

        if hasattr(res['value'], 'Errors') and res['value'].Errors:
            for error in res['value'].Errors.Error:
                message = '[%s] %s' % (error.Code, error.Message)
            raise orm.except_orm('Error', message)

        service_group_codes = []
        for group in res['value'].ServiceGroups:
            service_group_codes.append(group.ServiceGroup.ServiceGroupID)

        return service_group_codes

    def assign_licenses_to_service_groups(self, cr, uid, ids, context=None):
        """ Check all licenses to assign it to PostLogistics service groups """

        if context is None:
            context = {}

        service_group_obj = self.pool.get('postlogistics.service.group')
        for config in self.browse(cr, uid, ids, context=context):
            company = config.company_id
            web_service = PostlogisticsWebService(company)

            relations = {}
            for license in company.postlogistics_license_ids:
                service_groups = self._get_allowed_service_group_codes(
                    web_service, company, license, context=context)
                group_ids = service_group_obj.search(
                    cr, uid, [('group_extid', 'in', service_groups)],
                    context=context)
                for group_id in group_ids:
                    if group_id in relations:
                        relations[group_id].append(license.id)
                    else:
                        relations[group_id] = [license.id]
            for group_id, license_ids in relations.iteritems():
                vals = {'postlogistics_license_ids': [(6, 0, license_ids)]}
                service_group_obj.write(cr, uid, group_id, vals,
                                        context=context)
        return True
