# Copyright 2021 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
import logging
import threading
from pprint import pprint

from odoo.exceptions import UserError
from quickpac import (
    ApiClient,
    BarcodeApi,
    Configuration,
    GenerateLabelResponse,
    ZIPAllResponse,
    ZIPApi,
    ZIPIsCurrentResponse,
)

from .helpers import get_language, prepare_envelope

_logger = logging.getLogger("Quickpac API")


def _get_errors_from_response(response):
    """ Manage to get potential errors from a Response

    :param response: GenerateLabelResponse,ZIPAllResponse,ZIPIsCurrentResponse
    :return: list of string (formatted messages prefixing the type or empty)
    """
    if not response:
        return
    errors = []
    messages = []

    if isinstance(response, GenerateLabelResponse):
        items = response.envelope.data.provider.sending.item
        for item in items:
            if item.errors:
                errors.extend(item.errors)
    if isinstance(response, (ZIPAllResponse, ZIPIsCurrentResponse)):
        if response.errors:
            errors.extend(response.errors)

    for error in errors:
        message = error.code + " - " + error.message
        messages.append(message)

    return messages


def _get_warnings_from_response(response):
    """ Manage to get potential warnings from a Response

    :param response: GenerateLabelResponse,ZIPAllResponse,ZIPIsCurrentResponse
    :return: list of string (formatted messages prefixing the type or empty)
    """
    if not response:
        return
    warnings = []
    messages = []

    if isinstance(response, GenerateLabelResponse):
        items = response.envelope.data.provider.sending.item
        for item in items:
            if item.warnings:
                warnings.extend(item.warnings)
    if isinstance(response, (ZIPAllResponse, ZIPIsCurrentResponse)):
        if response.warnings:
            warnings.extend(response.warnings)

    for warning in warnings:
        message = warning.code + " - " + warning.message
        messages.append(message)

    return messages


def process_response(response):
    """ Process the response to find anything to be processed before rendering
    Such as errors, specific codes, etc.

    :param response: GenerateLabelResponse,ZIPAllResponse,ZIPIsCurrentResponse
    :raise: UserError
    """
    if not response:
        return
    errors = _get_errors_from_response(response)
    if errors:
        for error in errors:
            _logger.error(error)
        raise UserError(",\t".join(errors))
    warnings = _get_warnings_from_response(response)
    if warnings:
        for warning in warnings:
            _logger.warning(warning)
        raise UserError(",\t".join(warnings))


class QuickpacWebService(object):
    """ Connector with Quickpac for labels using their API

    Specification available here:
    https://api.quickpac.ch/swagger/index.html

    Allows to interact with the OpenAPI generated implementation
    """

    access_token = False
    access_token_expiry = False
    _lock = threading.Lock()

    def __init__(self, company):
        self.company = company
        configuration = Configuration()
        configuration.username = self.company.quickpac_username
        configuration.password = self.company.quickpac_password
        api_client = ApiClient(configuration)
        self.zip_api = ZIPApi(api_client)
        self.barcode_api = BarcodeApi(api_client)

    def get_valid_zipcodes(self):
        """ Return all valid zipcodes managed by Quickpac

        :raise: UserError if any errors occurs
        """
        zipcode_all_response = None
        try:
            zipcode_all_response = self.zip_api.z_ip_get_all_zip_codes_get()
            zipcode_models = zipcode_all_response.zip_codes
            return [zip.zip_code for zip in zipcode_models]
        except Exception as e:
            return []
        finally:
            process_response(zipcode_all_response)

    def is_deliverable_zipcode(self, zipcode):
        """ Check whether or not the deliverability of this zipcodes

        :param zipcode: zipcode to check
        :raise: UserError if any errors occurs
        """
        zipcode_response = None
        try:
            zipcode_response = self.zip_api.z_ip_is_deliverable_zip_code_get(
                zip_code=zipcode
            )
            return bool(zipcode_response.deliverable)
        except Exception as e:
            return False
        finally:
            process_response(zipcode_response)

    def generate_label(self, picking, packages):
        """ Generate a label for a picking

        :param picking: picking browse record
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
        lang = get_language(self.company.partner_id.lang)
        envelope = prepare_envelope(picking, self.company, packages)
        body = {"Language": lang, "Envelope": envelope}
        response = self.barcode_api.barcode_generate_label_post(body=body)
        process_response(response)
        items = response.envelope.data.provider.sending.item
        label_definition = response.envelope.label_definition
        file_type = label_definition.image_file_type.lower()
        labels = []
        for item in items:
            binary = base64.b64encode(bytes(item.label, 'utf-8'))
            res = {
                "success": True,
                "errors": [],
                "value": {
                    "item_id": item.item_id,
                    "binary": binary,
                    "tracking_number": item.ident_code,
                    "file_type": file_type,
                },
            }
            labels.append(res)
        return labels
