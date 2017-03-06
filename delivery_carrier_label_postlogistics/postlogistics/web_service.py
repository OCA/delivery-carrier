# -*- coding: utf-8 -*-
# © 2013-2016 Yannick Vaucher (Camptocamp SA)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import re
import logging
from urllib2 import HTTPSHandler
from PIL import Image
from StringIO import StringIO
import ssl

from openerp import exceptions, _

_logger = logging.getLogger(__name__)

try:
    from suds.xsd.doctor import Import, ImportDoctor
    from suds.client import Client, WebFault
    from suds.transport.http import HttpAuthenticated
    from suds.transport.https import HttpAuthenticated as HttpsAuth
    from suds.cache import NoCache
except ImportError:
    _logger.warning(
        'suds library not found. '
        'If you plan to use it, please install the suds library '
        'from https://pypi.python.org/pypi/suds')

_compile_itemid = re.compile(r'[^0-9A-Za-z+\-_]')
_compile_itemnum = re.compile(r'[^0-9]')


class IntegrationTransport(HttpsAuth):
    """ Transport for integration to works with self signed SSL certificates
    """

    def u2handlers(self):
        handlers = HttpsAuth.u2handlers(self)
        ssl_context = ssl._create_unverified_context()
        handlers.append(HTTPSHandler(context=ssl_context))
        return handlers


class PostlogisticsWebService(object):

    """ Connector with PostLogistics for labels using post.ch Web Services

    Handbook available here:
    https://www.post.ch/en/business/a-z-of-subjects/dropping-off-mail-items/business-sending-letters/barcode-web-service-documentation

    Allows to generate labels

    """

    def __init__(self, company):
        self.init_connection(company)

    def init_connection(self, company):
        if company.postlogistics_test_mode:
            # We must change location for namespace as suds will take the wrong
            # one and find nothing
            # In order to have the test_mode working, it is necessary to patch
            # suds with https://fedorahosted.org/suds/attachment/ticket/239/suds_recursion.patch # noqa
            ns = "https://int.wsbc.post.ch/wsbc/barcode/v2_2/types"
            location = "https://int.wsbc.post.ch/wsbc/barcode/v2_2?xsd=1"
            imp = Import(ns, location)
            doctor = ImportDoctor(imp)
            t = IntegrationTransport(
                username=company.postlogistics_username,
                password=company.postlogistics_password)
            self.client = Client(
                company.postlogistics_wsdl_url,
                transport=t,
                cache=NoCache(),
                doctor=doctor)
        else:
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
            # if authentication error
            if isinstance(e[0], tuple) and e[0][0] == 401:
                raise exceptions.UserError(
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

    def read_allowed_services_by_franking_license(self, cp_license, company,
                                                  lang=None):
        """ Get a list of allowed service for a postlogistics licence """
        if not lang:
            lang = company.partner_id.lang or 'en'
        lang = self._get_language(lang)
        request = self.client.service.ReadAllowedServicesByFrankingLicense
        return self._send_request(request, FrankingLicense=cp_license,
                                  Language=lang)

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
        return self._send_request(request, Language=lang,
                                  ServiceGroupID=service_group_id)

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

        if partner.street2:
            recipient['AddressSuffix'] = partner.street2

        if partner.parent_id:
            recipient['Name2'] = partner.parent_id.name
            recipient['PersonallyAddressed'] = False

        # Phone and / or mobile should only be diplayed if instruction to
        # Notify delivery by telephone is set
        is_phone_required = [option for option in picking.option_ids
                             if option.code == 'ZAW3213']
        if is_phone_required:
            phone = picking.delivery_phone or partner.phone
            if phone:
                recipient['Phone'] = phone

            mobile = picking.delivery_mobile or partner.mobile
            if mobile:
                recipient['Mobile'] = mobile

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
            label_layout = company.postlogistics_default_label_layout.code
        return label_layout

    def _get_output_format(self, picking):
        output_format = self._get_single_option(picking, 'output_format')
        if not output_format:
            company = picking.company_id
            output_format = company.postlogistics_default_output_format.code
        return output_format

    def _get_image_resolution(self, picking):
        resolution = self._get_single_option(picking, 'resolution')
        if not resolution:
            company = picking.company_id
            resolution = company.postlogistics_default_resolution.code
        return resolution

    def _get_license(self, picking):
        """ Get the license

        Take it from carrier and if not defined get the first license
        depending on service group. This needs to have associated
        licenses to groups.

        :return: license number
        """
        franking_license = picking.carrier_id.postlogistics_license_id
        if not franking_license:
            company_licenses = picking.company_id.postlogistics_license_ids
            group = picking.carrier_id.postlogistics_service_group_id
            if not company_licenses or not group:
                return None
            group_license_ids = [l.id for l in group.postlogistics_license_ids]
            if not group_license_ids:
                return None
            franking_license = [l for l in company_licenses
                                if l.id in group_license_ids][0]
        return franking_license.number

    def _prepare_attributes(self, picking, pack_num=None, pack_total=None):
        services = [option.code.split(',') for option in picking.option_ids
                    if option.tmpl_option_id.postlogistics_type
                    in ('basic', 'additional', 'delivery')]

        attributes = {
            'PRZL': services,
        }
        option_codes = [option.code for option in picking.option_ids]
        if 'ZAW3217' in option_codes and picking.delivery_fixed_date:
            attributes['DeliveryDate'] = picking.delivery_fixed_date
        if 'ZAW3218' in option_codes and pack_num:
            attributes.update({
                'ParcelTotal': pack_total or picking.number_of_packages,
                'ParcelNo': pack_num,
            })
        if 'ZAW3219' in option_codes and picking.delivery_place:
            attributes['DeliveryPlace'] = picking.delivery_place
        if picking.company_id.postlogistics_proclima_logo:
            attributes['ProClima'] = True
        return attributes

    def _get_itemid(self, picking, pack_no):
        """ Allowed characters are alphanumeric plus `+`, `-` and `_`
        Last `+` separates picking name and package number (if any)

        :return string: itemid

        """
        name = _compile_itemid.sub('', picking.name)
        if pack_no:
            pack_no = _compile_itemid.sub('', pack_no)
        codes = [name, pack_no]
        return "+".join(c for c in codes if c)

    def _cash_on_delivery(self, picking, package=None):
        if package:
            amount = package.postlogistics_cod_amount()
        else:
            amount = picking.postlogistics_cod_amount()
        amount = '{:.2f}'.format(amount)
        return [{'Type': 'NN_BETRAG', 'Value': amount}]

    def _get_item_additional_data(self, picking, package=None):
        result = []
        if set(picking.option_ids.mapped('code')) & {'BLN', 'N'}:
            cod_attributes = self._cash_on_delivery(picking, package=package)
            result += cod_attributes
        return result

    def _get_item_number(self, picking, pack_num):
        """ Generate the tracking reference for the last 8 digits
        of tracking number of the label.

        2 first digits for a pack counter
        6 last digits for the picking name

        e.g. 03000042 for 3rd pack of picking OUT/19000042
        """
        picking_num = _compile_itemnum.sub('', picking.name)
        return '%02d%s' % (pack_num, picking_num[-6:].zfill(6))

    def _prepare_item_list(self, picking, recipient, packages):
        """ Return a list of item made from the pickings """
        company = picking.company_id
        item_list = []
        pack_counter = 1

        def add_item(package=None):
            assert picking or package
            itemid = self._get_itemid(picking,
                                      package.name if package else picking.name
                                      )
            item = {
                'ItemID': itemid,
                'Recipient': recipient,
                'Attributes': attributes,
            }
            if company.postlogistics_tracking_format == 'picking_num':
                if not package:
                    # start with 9 to garentee uniqueness and use 7 digits
                    # of picking number
                    picking_num = _compile_itemnum.sub('', picking.name)
                    item_number = '9%s' % picking_num[-7:].zfill(7)
                else:
                    item_number = self._get_item_number(picking, pack_counter)
                item['ItemNumber'] = item_number

            additional_data = self._get_item_additional_data(picking,
                                                             package=package)
            if additional_data:
                item['AdditionalINFOS'] = {'AdditionalData': additional_data}

            item_list.append(item)

        if not packages:
            attributes = self._prepare_attributes(picking)
            add_item()

        pack_total = len(packages)
        for pack in packages:
            attributes = self._prepare_attributes(
                picking, pack_counter, pack_total)
            add_item(package=pack)
            pack_counter += 1

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
        error_missing = _(
            "You need to configure %s. You can set a default"
            "value in Settings/Configuration/Carriers/Postlogistics."
            " You can also set it on delivery method or on the picking."
        )
        label_layout = self._get_label_layout(picking)
        if not label_layout:
            raise exceptions.UserError(
                _('Layout not set') + '\n' +
                error_missing % _("label layout"))

        output_format = self._get_output_format(picking)
        if not output_format:
            raise exceptions.UserError(
                _('Output format not set') + '\n' +
                error_missing % _("output format"))

        image_resolution = self._get_image_resolution(picking)
        if not image_resolution:
            raise exceptions.UserError(
                _('Resolution not set') + '\n' +
                error_missing % _("resolution"))

        label_definitions = {
            'LabelLayout': label_layout,
            'PrintAddresses': 'RecipientAndCustomer',
            'ImageFileType': output_format,
            'ImageResolution': image_resolution,
            'PrintPreview': False,
        }
        license = self._get_license(picking)
        file_infos = {
            'FrankingLicense': license,
            'PpFranking': False,
            'CustomerSystem': 'Odoo',
            'Customer': post_customer,
        }

        envelope = {
            'LabelDefinition': label_definitions,
            'FileInfos': file_infos,
            'Data': data,
        }
        return envelope

    def generate_label(self, picking, packages, user_lang=None):
        """ Generate a label for a picking

        :param picking: picking browse record
        :param user_lang: OpenERP language code
        :param packages: list of browse records of packages to filter on
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
        if not user_lang:
            user_lang = 'en_US'
        lang = self._get_language(user_lang)
        post_customer = self._prepare_customer(picking)

        recipient = self._prepare_recipient(picking)
        item_list = self._prepare_item_list(picking, recipient, packages)
        data = self._prepare_data(item_list)

        envelope = self._prepare_envelope(picking, post_customer, data)

        output_format = self._get_output_format(picking).lower()

        res = {'value': []}
        request = self.client.service.GenerateLabel
        response = self._send_request(request, Language=lang,
                                      Envelope=envelope)

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
                file_type = output_format if output_format != 'spdf' else 'pdf'
                res['value'].append({
                    'item_id': item.ItemID,
                    'binary': item.Label,
                    'tracking_number': item.IdentCode,
                    'file_type': file_type,
                })

            if hasattr(item, 'Warnings') and item.Warnings:
                for warning in item.Warnings.Warning:
                    message = '[%s] %s' % (warning.Code, warning.Message)
                    warning_messages.append(message)

        if error_messages:
            res['errors'] = error_messages
        if warning_messages:
            res['warnings'] = warning_messages
        return res
