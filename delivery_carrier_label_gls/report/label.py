#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
TODO :
* test exception
* manage encodings
* convertir addresse en majuscule
"""

from mako.template import Template
from mako.exceptions import RichTraceback
from datetime import datetime
import time
from .label_helper import AbstractLabel
from .exception_helper import (InvalidSequence)
import httplib
from unidecode import unidecode
import logging
import os

REPORT_CODING = 'cp1252'
ERROR_BEHAVIOR = 'backslashreplace'
REPLACEMENT_STRING = ''
GLS_PORT = 80
WEB_SERVICE_CODING = 'ISO-8859-1'
LABEL_FILE_NAME = 'gls'

logger = logging.getLogger(__name__)

URL_PROD = "http://www.gls-france.com/cgi-bin/glsboxGI.cgi"
URL_TEST = "http://www.gls-france.com/cgi-bin/glsboxGITest.cgi"


COUNTRIES_PREFIX = ['AD', 'AE', 'AF', 'AG', 'AI', 'AL', 'AM', 'AN', 'AO', 'AQ', 'AR', 'AS', 'AT', 'AU', 'AW', 'AX', 'AZ', 'BA', 'BB', 'BD', 'BE', 'BF', 'BG', 'BH', 'BI', 'BJ', 'BL', 'BM', 'BN', 'BO', 'BQ', 'BR', 'BS', 'BT', 'BV', 'BW', 'BY', 'BZ', 'CA', 'CC', 'CD', 'CF', 'CG', 'CH', 'CI', 'CK', 'CL', 'CM', 'CN', 'CO', 'CR', 'CU', 'CV', 'CW', 'CX', 'CY', 'CZ', 'DE', 'DJ', 'DK', 'DM', 'DO', 'DZ', 'EC', 'EE', 'EG', 'EH', 'ER', 'ES', 'ET', 'FI', 'FJ', 'FK', 'FM', 'FO', 'FR', 'GA', 'GB', 'GD', 'GE', 'GF', 'GG', 'GH', 'GI', 'GL', 'GM', 'GN', 'GP', 'GQ', 'GR', 'GS', 'GT', 'GU', 'GW', 'GY', 'HK', 'HM', 'HN', 'HR', 'HT', 'HU', 'ID', 'IE', 'IL', 'IM', 'IN', 'IO', 'IQ', 'IR', 'IS', 'IT', 'JE', 'JM', 'JO', 'JP', 'KE', 'KG', 'KH', 'KI', 'KM', 'KN', 'KP', 'KR', 'KW', 'KY', 'KZ', 'LA', 'LB', 'LC', 'LI', 'LK', 'LR', 'LS', 'LT', 'LU', 'LV', 'LY', 'MA', 'MC', 'MD', 'ME', 'MF', 'MG', 'MH', 'MK', 'ML', 'MM', 'MN', 'MO', 'MP', 'MQ', 'MR', 'MS', 'MT', 'MU', 'MV', 'MW', 'MX', 'MY', 'MZ', 'NA', 'NC', 'NE', 'NF', 'NG', 'NI', 'NL', 'NO', 'NP', 'NR', 'NT', 'NU', 'NZ', 'OM', 'PA', 'PE', 'PF', 'PG', 'PH', 'PK', 'PL', 'PM', 'PN', 'PR', 'PS', 'PT', 'PW', 'PY', 'QA', 'RE', 'RO', 'RS', 'RU', 'RW', 'SA', 'SB', 'SC', 'SD', 'SE', 'SG', 'SH', 'SI', 'SJ', 'SK', 'SL', 'SM', 'SN', 'SO', 'SR', 'SS', 'ST', 'SV', 'SX', 'SY', 'SZ', 'TC', 'TD', 'TF', 'TG', 'TH', 'TJ', 'TK', 'TM', 'TN', 'TO', 'TP', 'TR', 'TT', 'TV', 'TW', 'TZ', 'UA', 'UG', 'UM', 'US', 'UY', 'UZ', 'VA', 'VC', 'VE', 'VG', 'VI', 'VN', 'VU', 'WF', 'WS', 'YE', 'YT', 'YU', 'ZA', 'ZM', 'ZR', 'ZW', 'ZW']


class InvalidDataForMako(Exception):
    ""


def GLS_countries_prefix():
    """For GLS carrier 'Serbie Montenegro' is 'CS' and for wikipedia it's 'ME'
    We have to do a quick replacement
    """
    GLS_prefix = COUNTRIES_PREFIX
    GLS_prefix[GLS_prefix.index('ME')] = 'CS'
    return GLS_prefix

GLS_COUNTRIES_PREFIX = GLS_countries_prefix()

EUROPEAN_COUNTRIES = ['AT','BE','BG','CY','CZ','DE','DK','ES','EE','FI','GR',
                      'GB','HU','IE','IT','LV','LT','LU', 'MT', 'NL', 'PL',
                      'PT','RO', 'SK', 'SI', 'SE']

# Here is all keys used in GLS templates
ADDRESS_MODEL = {
    "consignee_name":   {'max_size': 35, 'required': True},
    "street":           {'max_size': 35, 'required': True},
    "street2":          {'max_size': 35},
    "street3":          {'max_size': 35},
    "zip":              {'max_size': 10, 'required': True},
    "city":             {'max_size': 35, 'required': True},
    "country_code":     {'in': GLS_COUNTRIES_PREFIX, 'required': True},
    "consignee_phone":  {'max_size': 20},
    "consignee_mobile": {'max_size': 20},
    "consignee_email":  {'max_size': 100},
    # for uniship label only
    "country_norme3166": {'max_number': 999, 'min_number': 1, 'type': int},
}

PARCEL_MODEL = {
    "parcel_number_label":   {'max_number': 999, 'type': int, 'required': True},
    "parcel_number_barcode": {'max_number': 999, 'type': int, 'required': True},
    #TODO validate a weight of XX.XX (5 chars)  {0:05.2f}
    "weight":                {'max_size': 5, 'required': True},
}
DELIVERY_MODEL = {
    #'address': ADDRESS_MODEL,
    "consignee_ref":    {'max_size': 20},
    "contact":   {'max_size': 35},
    "additional_ref_1": {'max_size': 20},
    "additional_ref_2": {'max_size': 20},
    "shipping_date":    {'date': '%Y%m%d', 'required': True},
    "commentary":       {'max_size': 35},
    "parcel_total_number": {'max_number': 999, 'type': int, 'required': True},
    #TODO : valider 10 caract numériques
    "custom_sequence": {'max_size': 10, 'min_size': 10, 'required': True},
}
SENDER_MODEL = {
    "customer_id":       {'max_size': 10, 'required': True},
    "contact_id":        {'max_size': 10},
    "outbound_depot":    {'max_size': 6, 'required': True},
    "shipper_name":      {'max_size': 35, 'required': True},
    "shipper_street":    {'max_size': 35, 'required': True},
    "shipper_street2":   {'max_size': 35},
    "shipper_zip":       {'max_size': 10, 'required': True},
    "shipper_city":      {'max_size': 35, 'required': True},
    "shipper_country":   {'in': GLS_COUNTRIES_PREFIX, 'required': True},
    #"webservice_url":    {'max_size': 100, 'required': True},
}

# Here is all fields called in mako template
ADDRESS_MAPPING = {
    'T860': "consignee_name",
    'T863': "street",
    'T861': "street2",
    'T862': "street3",
    'T330': "zip",
    'T864': "city",
    'T100': "country_code",
    'T871': "consignee_phone",
    'T1230': "consignee_mobile",
    'T1229': "consignee_email",
}
PARCEL_MAPPING = {
    'T530': "weight",
    'T8973': "parcel_number_barcode",
    'T8904': "parcel_number_label",
}
DELIVERY_MAPPING = {
    #'address': ADDRESS_MODEL,
    'T859': "consignee_ref",
    'T854': "additional_ref_1",
    'T8907': "additional_ref_1",
    'T8908': "additional_ref_2",
    'T540': "shipping_date",
    #'T8906': "commentary", # define in doc
    'T8906': "contact",
    'T8318': "commentary",
    'T8975': "gls_origin_reference",
    'T8912': "gls_origin_reference",
    'T8905': "parcel_total_number", #TODO : valider 10 caract numériques
    'T8702': "parcel_total_number",
}
ACCOUNT_MAPPING = {
    'T8915': "customer_id",
    'T805': "customer_id",
    'T8914': "contact_id",
    'T8700': "outbound_depot",
    'T810': "shipper_name",
    'T811': "shipper_street",
    'T820': "shipper_street2",
    'T810': "shipper_name",
    'T822': "shipper_zip",
    'T823': "shipper_city",
    'T821': "shipper_country",
}

MAPPING = {}
MAPPING.update(ACCOUNT_MAPPING)
MAPPING.update(DELIVERY_MAPPING)
MAPPING.update(PARCEL_MAPPING)
MAPPING.update(ADDRESS_MAPPING)


def dict_to_gls_data(params):
    res = "\\\\\GLS\\\\\|"
    for key, val in params.items():
        if val != '':
            res += "%s:%s|" % (key, val)
    res += "/////GLS/////"
    return res


def gls_data_to_dict(data):
    res = {}
    for val in data.split('|')[1:-1]:
        key, value = val.split(':', 1)
        res[key] = value.decode(WEB_SERVICE_CODING, 'ignore')
    return res


def gls_decode(data):
    return gls_data_to_dict(data)


class Gls(AbstractLabel):

    def __init__(self, sender, code, test_plateform=False):
        self.check_model(sender, SENDER_MODEL, 'company')
        #self.product_code, self.uniship_product = self.get_product(
        #                                            account['shipper_country'])
        if test_plateform:
            url = URL_TEST
        else:
            url = URL_PROD
        url_separ = url.find('.com/') + 4
        start = 0
        if url[:7] == 'http://':
            start = 7
        self.webservice_location = url[start:url_separ]
        self.webservice_method = url[url_separ:]
        self.filename = LABEL_FILE_NAME
        self.sender = sender

    def add_specific_keys(self, address):
        res = {}
        res['T090'] = 'NOSAVE'
        res['T750'] = ''
        res['T200'] = ''
        res['T8977'] = ''   # RefDest
        if address['country_code'] == 'FR':
            res['T082'] = 'UNIQUENO'
        return res

    def get_barcode_uniship(self, all_dict, address):
        # get datas for uniship barcode
        if address['country_norme3166']:
            items = [
                'A',  # barcode version
                all_dict['T8915'],
                all_dict['T8914'],
                self.uniship_product,
                address['country_norme3166'],
                all_dict['T330'],    #postal code
                all_dict['T8905'],   #total parcel number
                all_dict['T8702'],   #total parcel number datamatrix
                all_dict['T8973'],   #sequence
                '',                  #ref expe
                all_dict['T860'],    #consignee name
                all_dict['T861'],    #supplément raison sociale1
                all_dict['T862'],    #supplément raison sociale2
                all_dict['T863'],    #street
                '',                  #N° de rue
                all_dict['T864'],    #city
                all_dict['T871'],    #tel
                '',                  #ref customer
                all_dict['T8975'],
                all_dict['T530'],    #weight
            ]
            code = '|'.join(items)+'|'
            #code needs to be fixed size
            code += (304 - len(code)) * ' '
            return {'T8917': code}
        else:
            #TODO : n'est pas ramené à l'erp
            raise Exception("There is no key 'country_norme3166' in the " +
                "given dictionnary 'address' for the country '%s' : " +
                " this data is required" % address['country_code'])

    def select_label(self, parcel, all_dict, address, failed_webservice=False):
        if address['country_code'] == 'FR' and not failed_webservice:
            self.filename = 'gls_rescue'
            zpl_file = 'label.mako'
        else:
            self.filename = 'gls_foreign'
            zpl_file = 'label_uniship.mako'
        self.filename += parcel
        template_path = os.path.join(os.path.dirname(__file__), zpl_file)
        with open(template_path, 'r') as template:
            content = template.read()
            all_dict.update(self.get_barcode_uniship(all_dict, address))
        return content

    def get_result_analysis(self, result, all_dict):
        component = result.split(':')
        code, message = component[0], component[1]
        if code == 'E000':
            return True
        else:
            logger.info("""Web service access problem :
code: %s ; message: %s ; result: %s""" % (code, message, result))
            if message == 'T330':
                zip_code = ''
                if all_dict['T330']:
                    zip_code = all_dict['T330']
                raise Exception(
                    "Postal code '%s' is wrong (relative to the "
                    "destination country)" % zip_code)
            elif message == 'T100':
                cnty_code = ''
                if all_dict['T100']:
                    cnty_code = all_dict['T100']
                raise Exception("Country code '%s' is wrong" % cnty_code)
            else:
                if code == 'E999':
                    logger.info("Unibox server (web service) is not responding")
                else:
                    logger.info("""
        >>> An unknown problem is happened : check network connection, webservice
accessibility, sent datas and so on""")
                logger.info("""
        >>> Rescue label will be printed instead of the standard label""")
            return False

    def get_label(self, delivery, address, parcel):
        self.check_model(delivery, DELIVERY_MODEL, 'delivery')
        self.check_model(parcel, PARCEL_MODEL, 'package')
        self.check_model(address, ADDRESS_MODEL, 'partner')
        self.product_code, self.uniship_product = self.get_product(
            address['country_code'])
        delivery['gls_origin_reference'] = self.set_origin_reference(
            delivery, address)
        # transfom human keys in GLS keys (with 'T' prefix)
        T_account = self.map_semantic_keys(ACCOUNT_MAPPING, self.sender)
        T_delivery = self.map_semantic_keys(DELIVERY_MAPPING, delivery)
        T_parcel = self.map_semantic_keys(PARCEL_MAPPING, parcel)
        T_address = self.map_semantic_keys(ADDRESS_MAPPING, address)
        # merge all datas
        all_dict = {}
        all_dict.update(T_account)
        all_dict.update(T_delivery)
        all_dict.update(T_parcel)
        all_dict.update(T_address)
        all_dict.update(self.add_specific_keys(address))
        if address['country_code'] != 'FR':
            label_content = self.select_label(
                parcel['parcel_number_label'], all_dict, address)
        else:
            failed_webservice = False
            # webservice
            response = self.get_webservice_response(all_dict)
            # refactor webservice response failed and webservice downed
            if isinstance(response, dict):
                if self.get_result_analysis(response['RESULT'], all_dict):
                    all_dict.update(response)
                else:
                    failed_webservice = True
                    label_content = self.select_label(
                        parcel['parcel_number_label'],
                        all_dict, address,
                    )
            else:
                failed_webservice = True
            label_content = self.select_label(
                parcel['parcel_number_label'], all_dict, address,
                failed_webservice=failed_webservice)
        # some keys are not defined by GLS but are in mako template
        # this add empty values to these keys
        keys_without_value = self.validate_mako(label_content, all_dict.keys())
        all_dict.update(dict(zip(keys_without_value, keys_without_value)))
        try:
            tpl = Template(label_content).render(**all_dict)
            content2print = tpl.encode(
                encoding=REPORT_CODING, errors=ERROR_BEHAVIOR)
            return {
                "content": content2print,
                "carrier_tracking_ref": delivery['gls_origin_reference'],
                'filename': self.filename
                }
        except:
            traceback = RichTraceback()
            for (filename, lineno, function, line) in traceback.traceback:
                print "File %s, line %s, in %s" % (filename, lineno, function)
                print line, "\n"
            raise InvalidDataForMako(
                "%s: %s"
                % (str(traceback.error.__class__.__name__), traceback.error))

    def get_webservice_response(self, params):
        request = dict_to_gls_data(params)
        connection = httplib.HTTPConnection(self.webservice_location, GLS_PORT)
        connection.request(
            "POST",
            self.webservice_method, request.encode(WEB_SERVICE_CODING, 'ignore'))
        response = connection.getresponse()
        if response.status != 200:
            #see http://docs.python.org/release/2.7/library/httplib.html,
            #search 100
            if response.status in ['503', '504']:
                return response.status
            raise Exception(
                "Error %s sending request: %s"
                % (response.status, response.reason))
        datas = response.read()
        connection.close()
        return gls_decode(datas)

    def map_semantic_keys(self, T_keys, datas):
        mapping = {}
        for T, semantic_key in T_keys.items():
            #':' and '|' are forbidden because are used by webservice
            val = datas[semantic_key].replace(':', ' ').replace('|', ' ')
            mapping[T] = unidecode(val).upper()
        return mapping

    def get_product(self, address_country):
        product_code = '01'
        if address_country == 'FR':
            product_code = '02'
            uniship_product_code = 'AA'
        elif address_country in EUROPEAN_COUNTRIES:
            uniship_product_code = 'CC'
        else:
            uniship_product_code = 'FF'
        return (product_code, uniship_product_code)

    def set_origin_reference(self, delivery, address):
        return (
            self.product_code
            + delivery['custom_sequence']
            + '0000'
            + address['country_code']
        )

    def validate_mako(self, template, available_keys):
        import re
        keys2match = []
        for match in re.findall('\$\{(.+?)\}+', template):
            keys2match.append(match)
        unmatch = list(set(keys2match) - set(available_keys))
        if len(unmatch) > 0:
            print "\nGLS carrier : these keys are defined in mako template ",
            "but without valid replacement values", unmatch, '\n'
        return unmatch
