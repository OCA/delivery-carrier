# Copyright 2013-2019 Yannick Vaucher (Camptocamp SA)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
import re
import logging
import json
import unidecode
import requests
import threading
from PIL import Image
from io import StringIO
from datetime import datetime, timedelta
from email.utils import parseaddr

from odoo import _, exceptions

_logger = logging.getLogger(__name__)

_compile_itemid = re.compile(r'[^0-9A-Za-z+\-_]')
_compile_itemnum = re.compile(r'[^0-9]')


def _sanitize_string(string):
    """Temporary fix, remove all non ascii char as the API
    weirdly doesn't support them in some cases.
    """
    return unidecode.unidecode(string)


class PostlogisticsWebService(object):

    """ Connector with PostLogistics for labels using post.ch API

    Handbook available here:
    https://developer.post.ch/en/digital-commerce-api
    https://wedec.post.ch/doc/swagger/index.html?url=https://wedec.post.ch/doc/api/barcode/v1/swagger.yaml#/Barcode/generateAddressLabel

    Allows to generate labels

    """

    access_token = False
    access_token_expiry = False
    _lock = threading.Lock()

    def __init__(self, company):
        self.default_lang = company.partner_id.lang or 'en'

    def _get_language(self, lang):
        """ Return a language to iso format from odoo format.

        `iso_code` field in res.lang is not mandatory thus not always set.
        Use partner language if available, otherwise use english

        :param partner: partner browse record
        :return: language code to use.

        """
        if not lang:
            lang = self.default_lang
        available_languages = ['de', 'en', 'fr', 'it']  # Given by API doc
        lang_code = lang.split('_')[0]
        if lang_code in available_languages:
            return lang_code
        return 'en'

    def _prepare_recipient(self, picking):
        """ Create a ns0:Recipient as a dict from a partner

        :param partner: partner browse record
        :return a dict containing data for ns0:Recipient

        """
        partner = picking.partner_id

        partner_name = partner.name or partner.parent_id.name
        email = parseaddr(partner.email)[1]
        recipient = {
            'name1': _sanitize_string(partner_name),
            'street': _sanitize_string(partner.street),
            'zip': partner.zip,
            'city': partner.city,
            'email': email or None,
        }

        if partner.country_id.code:
            recipient['country'] = partner.country_id.code.upper()

        if partner.street2:
            recipient['addressSuffix'] = _sanitize_string(partner.street2)

        if partner.parent_id and partner.parent_id.name != partner_name:
            recipient['name2'] = _sanitize_string(partner.parent_id.name)
            recipient['personallyAddressed'] = False

        # Phone and / or mobile should only be displayed if instruction to
        # Notify delivery by telephone is set
        is_phone_required = [option for option in picking.option_ids
                             if option.code == 'ZAW3213']
        if is_phone_required:
            phone = picking.delivery_phone or partner.phone
            if phone:
                recipient['phone'] = phone

            mobile = picking.delivery_mobile or partner.mobile
            if mobile:
                recipient['mobile'] = mobile

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
            'name1': _sanitize_string(partner.name),
            'street': _sanitize_string(partner.street),
            'zip': partner.zip,
            'city': partner.city,
            'country': partner.country_id.code,
            'domicilePostOffice': company.postlogistics_office,
        }
        logo = company.postlogistics_logo
        if logo:
            logo_image = Image.open(StringIO(logo.decode()))
            logo_format = logo_image.format
            customer['logo'] = logo.decode()
            customer['logoFormat'] = logo_format
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
            label_layout = company.postlogistics_label_layout.code
        return label_layout

    def _get_output_format(self, picking):
        output_format = self._get_single_option(picking, 'output_format')
        if not output_format:
            company = picking.company_id
            output_format = company.postlogistics_output_format.code
        return output_format

    def _get_image_resolution(self, picking):
        resolution = self._get_single_option(picking, 'resolution')
        if not resolution:
            company = picking.company_id
            resolution = company.postlogistics_resolution.code
        return resolution

    def _get_license(self, picking):
        """ Get the license

        Take it from carrier and if not defined get the first license.

        :return: license number
        """
        franking_license = picking.carrier_id.postlogistics_license_id
        if not franking_license:
            company_licenses = picking.company_id.postlogistics_license_ids
            if not company_licenses:
                return None
            franking_license = company_licenses[0]
        return franking_license.number

    def _prepare_attributes(self, picking, pack_num=None, pack_total=None):

        services = [
            code
            for codes in (
                option.code.split(',')
                for option in picking.option_ids
                if option.tmpl_option_id.postlogistics_type
                in ('basic', 'additional', 'delivery')
            )
            for code in codes
        ]
        if not services:
            raise exceptions.UserError(
                _('Missing required delivery option on picking.')
            )

        attributes = {
            'przl': services,
            'weight': picking.shipping_weight,
        }
        option_codes = [option.code for option in picking.option_ids]
        if 'ZAW3217' in option_codes and picking.delivery_fixed_date:
            attributes['deliveryDate'] = picking.delivery_fixed_date
        if 'ZAW3218' in option_codes and pack_num:
            attributes.update({
                'parcelTotal': pack_total or picking.number_of_packages,
                'parcelNo': pack_num,
            })
        if 'ZAW3219' in option_codes and picking.delivery_place:
            attributes['deliveryPlace'] = picking.delivery_place
        if picking.company_id.postlogistics_proclima_logo:
            attributes['proClima'] = True
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
                'itemID': itemid,
                'recipient': recipient,
                'attributes': attributes,
            }
            if company.postlogistics_tracking_format == 'picking_num':
                if not package:
                    # start with 9 to garentee uniqueness and use 7 digits
                    # of picking number
                    picking_num = _compile_itemnum.sub('', picking.name)
                    item_number = '9%s' % picking_num[-7:].zfill(7)
                else:
                    item_number = self._get_item_number(picking, pack_counter)
                item['itemNumber'] = item_number

            additional_data = self._get_item_additional_data(picking,
                                                             package=package)
            if additional_data:
                item['additionalData'] = additional_data

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

    def _prepare_label_definition(self, picking):
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

        return {
            'labelLayout': label_layout,
            'printAddresses': 'RECIPIENT_AND_CUSTOMER',
            'imageFileType': output_format,
            'imageResolution': image_resolution,
            'printPreview': False,
        }

    def _prepare_data(self, lang, frankingLicense, post_customer,
                      labelDefinition, item):
        return {
            "language": lang.upper(),
            "frankingLicense": frankingLicense,
            "ppFranking": False,
            "customer": post_customer,
            "customerSystem": None,
            "labelDefinition": labelDefinition,
            "sendingID": None,
            "item": item,
        }

    @classmethod
    def _request_access_token(cls, env):
        icp = env['ir.config_parameter'].sudo()
        client_id = icp.get_param('postlogistics.oauth.client_id')
        client_secret = icp.get_param('postlogistics.oauth.client_secret')
        authentication_url = icp.get_param(
            'postlogistics.oauth.authentication_url'
        )

        if not (client_id and client_secret):
            raise exceptions.UserError(
                _('Authorization Required\n\n'
                  'Please verify postlogistics client id and secret in:\n'
                  'Configuration -> Postlogistics'))

        response = requests.post(
            url=authentication_url,
            headers={'content-type': 'application/x-www-form-urlencoded'},
            data={
                'grant_type': 'client_credentials',
                'client_id': client_id,
                'client_secret': client_secret,
                'scope': 'WEDEC_BARCODE_READ',
            },
            timeout=60,
        )
        return response.json()

    @classmethod
    def get_access_token(cls, env):
        """Threadsafe access to token"""

        with cls._lock:
            now = datetime.now()

            if cls.access_token:
                # keep a safe margin on the expiration
                expiry = cls.access_token_expiry - timedelta(seconds=5)
                if now < expiry:
                    return cls.access_token

            response = cls._request_access_token(env)
            cls.access_token = response['access_token']

            if not (cls.access_token):
                raise exceptions.UserError(
                    _('Authorization Required\n\n'
                      'Please verify postlogistics client id and secret in:\n'
                      'Configuration -> Postlogistics'))

            cls.access_token_expiry = now + timedelta(seconds=response["expires_in"])
            return cls.access_token

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

        access_token = self.get_access_token(picking.env)

        # get options
        if not user_lang:
            user_lang = 'en_US'
        lang = self._get_language(user_lang)
        post_customer = self._prepare_customer(picking)
        recipient = self._prepare_recipient(picking)
        item_list = self._prepare_item_list(picking, recipient, packages)
        labelDefinition = self._prepare_label_definition(picking)
        frankingLicense = self._get_license(picking)

        labels = []
        for item in item_list:
            res = {'value': []}

            data = self._prepare_data(
                lang, frankingLicense, post_customer, labelDefinition, item
            )
            icp = picking.env['ir.config_parameter']
            generate_label_url = icp.get_param(
                'postlogistics.oauth.generate_label_url'
            )
            response = requests.post(
                url=generate_label_url,
                headers={
                    'Authorization': 'Bearer %s' % access_token,
                    'accept': 'application/json',
                    'content-type': 'application/json',
                },
                data=json.dumps(data),
                timeout=60,
            )

            if response.status_code != 200:
                res['success'] = False
                res['errors'] = [
                    _('Error when communicating with swisspost API: %s') %
                    response.content.decode("utf-8")
                ]
                labels.append(res)
                break

            response_dict = json.loads(response.content.decode("utf-8"))

            if response_dict['item'].get('errors'):
                res['success'] = False
                res['errors'] = []
                for error in response_dict['item']['errors']:
                    res['errors'].append(
                        _(
                            'Swisspost API returns errors:\n'
                            'Error code: %s\n'
                            'Error message: %s'
                        ) % (error['code'], error['message'])
                    )
                labels.append(res)
                break

            output_format = self._get_output_format(picking).lower()
            file_type = output_format if output_format != 'spdf' else 'pdf'
            binary = base64.b64encode(bytes(response_dict['item']['label'][0], 'utf-8'))
            res['success'] = True
            res['value'] = {
                'item_id': item['itemID'],
                'binary': binary,
                'tracking_number': response_dict['item']['identCode'],
                'file_type': file_type,
            }
            labels.append(res)
        return labels
