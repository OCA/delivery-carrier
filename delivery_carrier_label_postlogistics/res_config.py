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

from openerp import models, fields, api, exceptions, _

from .postlogistics.web_service import PostlogisticsWebService

_logger = logging.getLogger(__name__)


class PostlogisticsConfigSettings(models.TransientModel):
    _name = 'postlogistics.config.settings'
    _inherit = 'res.config.settings'

    def _default_company(self):
        return self.env.user.company_id

    company_id = fields.Many2one(comodel_name='res.company',
                                 string='Company',
                                 required=True,
                                 default=_default_company)
    wsdl_url = fields.Char(related='company_id.postlogistics_wsdl_url')
    username = fields.Char(related='company_id.postlogistics_username')
    password = fields.Char(related='company_id.postlogistics_password')
    license_ids = fields.One2many(
        related='company_id.postlogistics_license_ids',
    )
    logo = fields.Binary(related='company_id.postlogistics_logo')
    office = fields.Char(related='company_id.postlogistics_office')

    default_label_layout = fields.Many2one(
        related='company_id.postlogistics_default_label_layout',
    )
    default_output_format = fields.Many2one(
        related='company_id.postlogistics_default_output_format',
    )
    default_resolution = fields.Many2one(
        related='company_id.postlogistics_default_resolution',
    )

    @api.onchange('company_id')
    def onchange_company_id(self):
        # update related fields
        if not self.company_id:
            return
        company = self.company_id

        licenses = company.postlogistics_license_ids
        label_layout = company.postlogistics_default_label_layout
        output_format = company.postlogistics_default_output_format
        resolution = company.postlogistics_default_resolution

        self.username = company.postlogistics_username
        self.password = company.postlogistics_password
        self.license_ids = licenses
        self.logo = company.postlogistics_logo
        self.office = company.postlogistics_office
        self.default_label_layout = label_layout
        self.default_output_format = output_format
        self.default_resolution = resolution

    @api.model
    def _get_delivery_instructions(self, web_service, company, service_code):
        lang = self.env.context.get('lang', 'en')
        service_code_list = service_code.split(',')
        res = web_service.read_delivery_instructions(company,
                                                     service_code_list,
                                                     lang)
        if 'errors' in res:
            errors = '\n'.join(res['errors'])
            error_message = (_('Could not retrieve Postlogistics delivery '
                               'instructions:\n%s') % errors)
            raise exceptions.Warning(error_message)

        if not res['value']:
            return {}

        if hasattr(res['value'], 'Errors') and res['value'].Errors:
            for error in res['value'].Errors.Error:
                message = '[%s] %s' % (error.Code, error.Message)
            raise exceptions.Warning(message)

        delivery_instructions = {}
        for service in res['value'].DeliveryInstructions:
            service_code = service.PRZL
            delivery_instructions[service_code] = {'name': service.Description}

        return delivery_instructions

    @api.model
    def _update_delivery_instructions(self, web_service, additional_services):
        carrier_option_obj = self.env['delivery.carrier.template.option']

        xmlid = 'delivery_carrier_label_postlogistics.postlogistics'
        postlogistics_partner = self.env.ref(xmlid)

        for service_code, data in additional_services.iteritems():
            options = carrier_option_obj.search(
                [('code', '=', service_code),
                 ('postlogistics_type', '=', 'delivery')
                 ]
            )

            if options:
                options.write(data)
            else:
                data.update(code=service_code,
                            postlogistics_type='delivery',
                            partner_id=postlogistics_partner.id)
                carrier_option_obj.create(data)
        lang = self.env.context.get('lang', 'en')
        _logger.info("Updated delivery instructions. [%s]", lang)

    @api.model
    def _get_additional_services(self, web_service, company, service_code):
        lang = self.env.context.get('lang', 'en')
        service_code_list = service_code.split(',')
        res = web_service.read_additional_services(company,
                                                   service_code_list,
                                                   lang)
        if 'errors' in res:
            errors = '\n'.join(res['errors'])
            error_message = (_('Could not retrieve Postlogistics base '
                               'services:\n%s') % errors)
            raise exceptions.Warning(error_message)

        if not res['value']:
            return {}

        if hasattr(res['value'], 'Errors') and res['value'].Errors:
            for error in res['value'].Errors.Error:
                message = '[%s] %s' % (error.Code, error.Message)
            raise exceptions.Warning(message)

        additional_services = {}
        for service in res['value'].AdditionalService:
            service_code = service.PRZL
            additional_services[service_code] = {'name': service.Description}

        return additional_services

    @api.model
    def _update_additional_services(self, web_service, additional_services):
        carrier_option_obj = self.env['delivery.carrier.template.option']

        xmlid = 'delivery_carrier_label_postlogistics.postlogistics'
        postlogistics_partner = self.env.ref(xmlid)

        for service_code, data in additional_services.iteritems():
            options = carrier_option_obj.search(
                [('code', '=', service_code),
                 ('postlogistics_type', '=', 'additional')
                 ])

            if options:
                options.write(data)
            else:
                data.update(code=service_code,
                            postlogistics_type='additional',
                            partner_id=postlogistics_partner.id)
                carrier_option_obj.create(data)
        lang = self.env.context.get('lang', 'en')
        _logger.info("Updated additional services [%s]", lang)

    @api.model
    def _update_basic_services(self, web_service, company, group):
        """ Update of basic services

        A basic service can be part only of one service group

        :return: {additional_services: {<service_code>: service_data}
                  delivery_instructions: {<service_code>: service_data}
                  }

        """
        carrier_option_obj = self.env['delivery.carrier.template.option']

        xmlid = 'delivery_carrier_label_postlogistics.postlogistics'
        postlogistics_partner = self.env.ref(xmlid)
        lang = self.env.context.get('lang', 'en')

        res = web_service.read_basic_services(company, group.group_extid, lang)
        if 'errors' in res:
            errors = '\n'.join(res['errors'])
            error_message = (_('Could not retrieve Postlogistics base '
                               'services:\n%s') % errors)
            raise exceptions.Warning(error_message)

        additional_services = {}
        delivery_instructions = {}
        # Create or update basic service
        for service in res['value'].BasicService:
            service_code = ','.join(service.PRZL)
            options = carrier_option_obj.search(
                [('code', '=', service_code),
                 ('postlogistics_service_group_id', '=', group.id),
                 ('postlogistics_type', '=', 'basic')
                 ]
            )
            data = {'name': service.Description}
            if options:
                options.write(data)
                option = options[0]
            else:
                data.update(code=service_code,
                            postlogistics_service_group_id=group.id,
                            partner_id=postlogistics_partner.id,
                            postlogistics_type='basic')
                option = carrier_option_obj.create(data)

            # Get related services
            allowed_services = self._get_additional_services(web_service,
                                                             company,
                                                             service_code)
            for key, value in additional_services.iteritems():
                if key in allowed_services:
                    field = 'postlogistics_basic_service_ids'
                    additional_services[key][field][0][2].append(option.id)
                    del allowed_services[key]
            for key, value in allowed_services.iteritems():
                field = 'postlogistics_basic_service_ids'
                value[field] = [(6, 0, [option.id])]
                additional_services[key] = value

            allowed_services = self._get_delivery_instructions(web_service,
                                                               company,
                                                               service_code)
            for key, value in delivery_instructions.iteritems():
                if key in allowed_services:
                    field = 'postlogistics_basic_service_ids'
                    delivery_instructions[key][field][0][2].append(option.id)
                    del allowed_services[key]
            for key, value in allowed_services.iteritems():
                field = 'postlogistics_basic_service_ids'
                value[field] = [(6, 0, [option.id])]
                delivery_instructions[key] = value

        _logger.info("Updated '%s' basic service [%s].", group.name, lang)
        return {'additional_services': additional_services,
                'delivery_instructions': delivery_instructions}

    @api.model
    def _update_service_groups(self, web_service, company):
        """ Also updates additional services and delivery instructions
        as they are shared between groups

        """
        service_group_obj = self.env['postlogistics.service.group']

        lang = self.env.context.get('lang', 'en')

        res = web_service.read_service_groups(company, lang)
        if 'errors' in res:
            errors = '\n'.join(res['errors'])
            error_message = (_('Could not retrieve Postlogistics group '
                               'services:\n%s') % errors)
            raise exceptions.Warning(error_message)

        additional_services = {}
        delivery_instructions = {}

        # Create or update groups
        for group in res['value'].ServiceGroup:
            group_extid = group.ServiceGroupID
            groups = service_group_obj.search(
                [('group_extid', '=', group_extid)],
            )
            data = {'name': group.Description}
            if groups:
                groups.write(data)
                group = groups[0]
            else:
                data['group_extid'] = group_extid
                group = service_group_obj.create(data)

            # Get related services for all basic services of this group
            res = self._update_basic_services(web_service, company, group)

            allowed_services = res.get('additional_services', {})
            for key, value in additional_services.iteritems():
                if key in allowed_services:
                    field = 'postlogistics_basic_service_ids'
                    option_ids = allowed_services[key][field][0][2]
                    additional_services[key][field][0][2].extend(option_ids)
                    del allowed_services[key]
            additional_services.update(allowed_services)

            allowed_services = res.get('delivery_instructions', {})
            for key, value in delivery_instructions.iteritems():
                if key in allowed_services:
                    field = 'postlogistics_basic_service_ids'
                    option_ids = allowed_services[key][field][0][2]
                    delivery_instructions[key][field][0][2].extend(option_ids)
                    del allowed_services[key]
            delivery_instructions.update(allowed_services)

        # Update related services
        self._update_additional_services(web_service, additional_services)
        self._update_delivery_instructions(web_service,
                                           delivery_instructions,)

    @api.multi
    def update_postlogistics_options(self):
        """ This action will update all postlogistics option by
        importing services from PostLogistics WebService API

        The object we create are 'delivey.carrier.template.option'

        """
        for config in self:
            company = config.company_id
            web_service = PostlogisticsWebService(company)

            # make sure we create source text in en_US
            ctx = self.env.context.copy()
            ctx['lang'] = 'en_US'
            self._update_service_groups(web_service, company)

            language_obj = self.env['res.lang']
            languages = language_obj.search([])

            # handle translations
            # we call the same method with a different language context
            for lang in languages:
                lang_code = lang.code
                postlogistics_lang = web_service._get_language(lang_code)
                # add translations only for languages that exists on
                # postlogistics, english source will be kept for other
                # languages
                if postlogistics_lang == 'en':
                    continue
                self.with_context(lang=lang_code)._update_service_groups(
                    web_service, company
                )
        return True

    @api.model
    def _get_allowed_service_group_codes(self, web_service, company,
                                         cp_license):
        """ Get a list of allowed service group codes"""
        lang = self.env.context.get('lang', 'en')
        res = web_service.read_allowed_services_by_franking_license(
            cp_license.number, company, lang)
        if 'errors' in res:
            errors = '\n'.join(res['errors'])
            error_message = (_('Could not retrieve allowed Postlogistics '
                               'service groups for the %s licence:\n%s')
                             % (cp_license.name, errors))
            raise exceptions.Warning(error_message)

        if not res['value']:
            return []

        if hasattr(res['value'], 'Errors') and res['value'].Errors:
            for error in res['value'].Errors.Error:
                message = '[%s] %s' % (error.Code, error.Message)
            raise exceptions.Warning(message)

        service_group_codes = []
        for group in res['value'].ServiceGroups:
            service_group_codes.append(group.ServiceGroup.ServiceGroupID)

        return service_group_codes

    @api.multi
    def assign_licenses_to_service_groups(self):
        """ Check all licenses to assign it to PostLogistics service groups """
        service_group_obj = self.env['postlogistics.service.group']
        license_obj = self.env['postlogistics.license']
        for config in self:
            company = config.company_id
            web_service = PostlogisticsWebService(company)

            relations = {}
            for cp_license in company.postlogistics_license_ids:
                service_groups = self._get_allowed_service_group_codes(
                    web_service, company, cp_license
                )
                groups = service_group_obj.search(
                    [('group_extid', 'in', service_groups)],
                )
                for group in groups:
                    relations.setdefault(group, license_obj.browse())
                    relations[group] |= cp_license
            for group, licenses in relations.iteritems():
                vals = {'postlogistics_license_ids': [(6, 0, licenses.ids)]}
                group.write(vals)
        return True
