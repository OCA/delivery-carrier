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
import re
from suds.client import Client, WebFault
from suds.transport.http import HttpAuthenticated
from PIL import Image
from StringIO import StringIO

from openerp.osv import orm
from openerp.tools.translate import _

_compile_itemid = re.compile('[^0-9A-Za-z+\-_]')


class PostlogisticsWebService(object):
    """ Connector with PostLogistics for labels using post.ch Web Services

    Handbook available here: http://www.poste.ch/post-barcode-cug.htm

    Allows to generate labels

    """

    def __init__(self, company):
        self.init_connection(company)

    def init_connection(self, company):
        t = HttpAuthenticated(
            username=company.postlogistics_username,
            password=company.postlogistics_password)
        self.client = Client(
            company.postlogistics_wsdl_url,
            transport=t)

    def _send_request(self, request, **kwargs):
        """ Wrapper for API requests

        :param request: callback for API request
        :param **kwargs: params forwarded to the callback

        """
        res = {}
        try:
            res['value'] = request(**kwargs)
            res['success'] = True
        except WebFault as e:
            res['success'] = False
            res['errors'] = [e[0]]
        except Exception as e:
            # if authentification error
            if isinstance(e[0], tuple) and e[0][0] == 401:
                raise orm.except_orm(
                    _('Error 401'),
                    _('Authorization Required\n\n'
                    'Please verify postlogistics username and password in:\n'
                    'Configuration -> Postlogistics'))
            raise
        return res

    def _get_language(self, lang):
        """ Return a language to iso format from openerp format.

        `iso_code` field in res.lang is not mandatory thus not always set.
        Use partner language if available, otherwise use english

        :param partner: partner browse record
        :return: language code to use.

        """
        available_languages = self.client.factory.create('ns0:Language')
        lang_code = lang.split('_')[0]
        if lang_code in available_languages:
            return lang_code
        return 'en'

    def read_allowed_services_by_franking_license(self, license, company, lang=None):
        """ Get a list of allowed service for a postlogistics licence """
        if not lang:
            lang = company.partner_id.lang
        lang = self._get_language(lang)
        request = self.client.service.ReadAllowedServicesByFrankingLicense
        return self._send_request(request, License=license, Language=lang)

    def read_service_groups(self, company, lang):
        """ Get group of services """
        if not lang:
            lang = company.partner_id.lang
        lang = self._get_language(lang)
        request = self.client.service.ReadServiceGroups
        return self._send_request(request, Language=lang)

    def read_basic_services(self, company, service_group_id, lang):
        """ Get basic services for a given service group """
        if not lang:
            lang = company.partner_id.lang
        lang = self._get_language(lang)
        request = self.client.service.ReadBasicServices
        return self._send_request(request, Language=lang, ServiceGroupID=service_group_id)

    def read_additional_services(self, company, service_code, lang):
        """ Get additional services compatible with a basic services """
        if not lang:
            lang = company.partner_id.lang
        lang = self._get_language(lang)
        request = self.client.service.ReadAdditionalServices
        return self._send_request(request, Language=lang, PRZL=service_code)

    def read_delivery_instructions(self, company, service_code, lang):
        """ Get delivery instruction 'ZAW' compatible with a base service """
        if not lang:
            lang = company.partner_id.lang
        lang = self._get_language(lang)
        request = self.client.service.ReadDeliveryInstructions
        return self._send_request(request, Language=lang, PRZL=service_code)

    def _prepare_recipient(self, picking):
        """ Create a ns0:Recipient as a dict from a partner

        :param partner: partner browse record
        :return a dict containing data for ns0:Recipient

        """
        partner = picking.partner_id

        recipient = {
            'Name1': partner.name,
            'Street': partner.street,
            'ZIP': partner.zip,
            'City': partner.city,
            'Country': partner.country_id.code,
            'EMail': partner.email or None,
        }

        if partner.parent_id:
            recipient['Name2'] = partner.parent_id.name
            recipient['PersonallyAddressed'] = False

        # Phone and / or mobile should only be diplayed if instruction to
        # Notify delivery by telephone is set
        is_phone_required = [option for option in picking.option_ids
                             if option.code == 'ZAW3213']
        if is_phone_required:
            if partner.phone:
                recipient['Phone'] = partner.phone

            if partner.mobile:
                recipient['Mobile'] = partner.mobile

        # XXX
        #if partner.POBox
            #customer['POBox'] = partner.email

        return recipient

    def _prepare_customer(self, picking):
        """ Create a ns0:Customer as a dict from picking

        This is the Postlogistic Customer, thus the sender

        :param picking: picking browse record
        :return a dict containing data for ns0:Customer

        """
        company = picking.company_id
        partner = company.partner_id

        customer = {
            'Name1': partner.name,
            'Street': partner.street,
            'ZIP': partner.zip,
            'City': partner.city,
            'Country': partner.country_id.code,
            'DomicilePostOffice': company.postlogistics_office,
        }
        logo_format = None
        logo = company.postlogistics_logo
        if logo:
            logo_image = Image.open(StringIO(logo.decode('base64')))
            logo_format = logo_image.format
            customer['Logo'] = logo
            customer['LogoFormat'] = logo_format
        return customer

    def _get_single_option(self, picking, option):
        option = [opt.code for opt in picking.option_ids
                  if opt.postlogistics_type == option]
        assert len(option) <= 1
        return option and option[0]

    def _get_label_layout(self, picking):
        label_layout = self._get_single_option(picking, 'label_layout')
        if not label_layout:
            company = picking.company_id
            label_layout = company.postlogistics_default_output_format
        return label_layout

    def _get_output_format(self, picking):
        output_format = self._get_single_option(picking, 'output_format')
        if not output_format:
            company = picking.company_id
            output_format = company.postlogistics_default_output_format
        return output_format

    def _get_image_resolution(self, picking):
        resolution = self._get_single_option(picking, 'resolution')
        if not resolution:
            company = picking.company_id
            resolution = company.postlogistics_default_resolution
        return resolution

    def _get_license(self, picking):
        """ Get the right license depending on weight """
        company = picking.company_id
        #XXX get weight or set it as an option on picking
        weight = 0
        if weight > 1.0:
            return company.postlogistics_license_more_1kg
        return company.postlogistics_license_less_1kg

    def _prepare_attributes(self, picking):
        services = [option.code.split(',') for option in picking.option_ids
                    if option.tmpl_option_id.postlogistics_type
                    in ('basic', 'additional', 'delivery')]

        attributes = {
            'PRZL': services,
        }
        return attributes

    def _get_itemid(self, picking, pack_no):
        """ Allowed characters are alphanumeric plus `+`, `-` and `_`
        Last `+` separates picking name and package number

        :return string: itemid

        """
        name = _compile_itemid.sub('', picking.name)
        return name + '+' + str(pack_no)

    def _prepare_item_list(self, picking, recipient, attributes):
        """ Return a list of item made from the pickings """
        item_list = []
        for pack_no in range(picking.number_of_packages or 1):
            item_id = self._get_itemid(picking, pack_no)
            item = {
                'ItemID': item_id,
                'Recipient': recipient,
                'Attributes': attributes,
            }

            item_list.append(item)

        return item_list

    def _prepare_data(self, item_list):
        sending = {
            'Item': item_list,
        }
        provider = {
            'Sending': sending
        }
        data = {
            'Provider': provider,
        }
        return data

    def _prepare_envelope(self, picking, post_customer, data):
        """ Define envelope for label request """
        label_layout = self._get_label_layout(picking)
        output_format = self._get_output_format(picking)
        image_resolution = self._get_image_resolution(picking)

        label_definitions = {
            'LabelLayout': label_layout,
            'PrintAddresses': 'RecipientAndCustomer',
            'ImageFileType': output_format,
            'ImageResolution': image_resolution,  #XXX
            'PrintPreview': False,
            }
        license = self._get_license(picking)
        file_infos = {
            'FrankingLicense': license,
            'PpFranking': False,
            'CustomerSystem': 'OpenERP',
            'Customer': post_customer,
            }

        envelope = {
            'LabelDefinition': label_definitions,
            'FileInfos': file_infos,
            'Data': data,
            }
        return envelope

    def generate_label(self, picking, user_lang='en_US'):
        """ Generate a label for a picking

        :param picking: picking browse record
        :param lang: OpenERP language code
        :return: {
            value: [{item_id: pack id
                     binary: file returned by API
                     tracking_number: id number for tracking
                     file_type: str of file type
                     }
                    ]
            errors: list of error message if any
            warnings: list of warning message if any
        }

        """
        # get options
        lang = self._get_language(user_lang)
        post_customer = self._prepare_customer(picking)

        attributes = self._prepare_attributes(picking)

        recipient = self._prepare_recipient(picking)
        item_list = self._prepare_item_list(picking, recipient, attributes)
        data = self._prepare_data(item_list)

        envelope = self._prepare_envelope(picking, post_customer, data)

        output_format = self._get_output_format(picking)

        res = {'value': []}
        request = self.client.service.GenerateLabel
        response = self._send_request(request, Language=lang, Envelope=envelope)

        if not response['success']:
            return response
        error_messages = []
        warning_messages = []
        for item in response['value'].Data.Provider.Sending.Item:
            if hasattr(item, 'Errors') and item.Errors:
                for error in item.Errors.Error:
                    message = '[%s] %s' % (error.Code, error.Message)
                    error_messages.append(message)
            else:
                res['value'].append({
                    'item_id': item.ItemID,
                    'binary': item.Label,
                    'tracking_number': item.IdentCode,
                    'file_type': output_format,
                })

            if hasattr(item, 'Warnings') and item.Warnings:
                for warning in item.Warnings:
                    message = '[%s] %s' % (warning.Code, warning.Message)
                    warning_messages.append(message)

        if error_messages:
            res['errors'] = error_messages
        if warning_messages:
            res['warnings'] = warning_messages
        return res
