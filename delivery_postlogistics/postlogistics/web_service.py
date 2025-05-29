# Copyright 2013 Yannick Vaucher (Camptocamp SA)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
import json
import logging
import re
import threading
import urllib.parse
from datetime import datetime, timedelta
from json import JSONDecodeError

import requests
from typing_extensions import deprecated

from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

_compile_itemid = re.compile(r"[^0-9A-Za-z+\-_]")
_compile_itemnum = re.compile(r"[^0-9]")
AUTH_PATH = "/WEDECOAuth/token"
GENERATE_LABEL_PATH = "/api/barcode/v1/generateAddressLabel"

DISALLOWED_CHARS_MAPPING = {
    "|": "",
    "\\": "",
    "<": "",
    ">": "",
    "\u2018": "'",
    "\u2019": "'",
}


def sanitize_string(value, mapping=None):
    """Remove disallowed characters ("|", "\", "<", ">", "’", "‘") from a string

    :param value: string to sanitize
    :param mapping: dict of disallowed characters to remove
    :return: sanitized string

    """
    mapping = mapping or DISALLOWED_CHARS_MAPPING
    value = value or ""
    for char, repl in mapping.items():
        value = value.replace(char, repl)
    return value


class PostlogisticsWebService:
    """Connector with PostLogistics for labels using post.ch API

    Handbook available here:
    https://developer.post.ch/en/digital-commerce-api
    https://wedec.post.ch/doc/swagger/index.html?
        url=https://wedec.post.ch/doc/api/barcode/v1/swagger.yaml
        #/Barcode/generateAddressLabel

    Allows to generate labels

    """

    access_token = False
    access_token_expiry = False
    _lock = threading.Lock()

    def __init__(self, company):
        self.default_lang = company.partner_id.lang or "en"

    def _get_language(self, lang):
        """Return a language to iso format from odoo format.

        `iso_code` field in res.lang is not mandatory thus not always set.
        Use partner language if available, otherwise use english

        :param partner: partner browse record
        :return: language code to use.

        """
        if not lang:
            lang = self.default_lang
        available_languages = ["de", "en", "fr", "it"]  # Given by API doc
        lang_code = lang.split("_")[0]
        if lang_code in available_languages:
            return lang_code
        return "en"

    def _get_label_layout(self, picking):
        """
        Get Label layout define in carrier
        """
        return picking.carrier_id.postlogistics_label_layout.code

    def _get_output_format(self, picking):
        """
        Get Output format define in carrier
        """
        return picking.carrier_id.postlogistics_output_format.code

    def _get_image_resolution(self, picking):
        """
        Get Output Resolution Code define in carrier
        """
        return picking.carrier_id.postlogistics_resolution.code

    def _get_license(self, picking):
        """Get the license

        Take it from carrier and if not defined get the first license.

        :return: license number
        """
        franking_license = picking.carrier_id.postlogistics_license_id
        return franking_license.number

    def _get_itemid(self, picking, package):
        """Allowed characters are alphanumeric plus `+`, `-` and `_`
        Last `+` separates picking name and package number (if any)

        :return string: itemid

        """
        name = _compile_itemid.sub("", picking.name)
        if not package:
            return name

        pack_no = _compile_itemid.sub("", package.name)
        codes = [name, pack_no]
        return "+".join(c for c in codes if c)

    def _prepare_data(
        self, lang, frankingLicense, post_customer, labelDefinition, item
    ):
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

    def _get_item_number(self, picking, package, index=1):
        """Generate the tracking reference for the last 8 digits
        of tracking number of the label.

        2 first digits for a pack counter
        6 last digits for the picking name

        e.g. 03000042 for 3rd pack of picking OUT/19000042
        """
        picking_num = _compile_itemnum.sub("", picking.name)
        package_number = picking.get_package_number_hook(package)
        if not package_number:
            package_number = index
        return "%02d%s" % (package_number, picking_num[-6:].zfill(6))

    def _prepare_item_list(self, picking, recipient, packages):
        """Return a list of item made from the pickings"""
        carrier = picking.carrier_id
        item_list = []

        def add_item(index=1, package=None):
            assert picking or package
            itemid = self._get_itemid(picking, package)
            item = {
                "itemID": itemid,
                "recipient": recipient,
                "attributes": attributes,
            }
            if carrier.postlogistics_tracking_format == "picking_num":
                if not package:
                    # start with 9 to ensure uniqueness and use 7 digits
                    # of picking number
                    picking_num = _compile_itemnum.sub("", picking.name)
                    item_number = f"9{picking_num[-7:].zfill(7)}"
                else:
                    item_number = self._get_item_number(picking, package, index)
                item["itemNumber"] = item_number

            additional_data = picking.postlogistics_label_get_item_additional_data(
                package=package
            )
            if additional_data:
                item["additionalData"] = additional_data

            item_list.append(item)

        total_packages = len(packages)
        for index, package in enumerate(packages):
            package_number = picking.get_package_number_hook(package)
            if not package_number:
                package_number = index + 1
            attributes = picking.postlogistics_label_prepare_attributes(
                pack=package, pack_num=package_number, pack_total=total_packages
            )
            add_item(package_number, package=package)
        else:
            attributes = picking.postlogistics_label_prepare_attributes()
            add_item()
        return item_list

    def _prepare_label_definition(self, picking):
        error_missing = picking.env._(
            "You need to configure %s. You can set a default"
            " value in Inventory / Configuration / Delivery / Shipping Methods."
            " You can also set it on delivery method or on the picking."
        )
        label_layout = self._get_label_layout(picking)
        if not label_layout:
            raise UserError(
                picking.env._("Layout not set")
                + "\n"
                + error_missing % picking.env._("label layout")
            )

        output_format = self._get_output_format(picking)
        if not output_format:
            raise UserError(
                picking.env._("Output format not set")
                + "\n"
                + error_missing % picking.env._("output format")
            )

        image_resolution = self._get_image_resolution(picking)
        if not image_resolution:
            raise UserError(
                picking.env._("Resolution not set")
                + "\n"
                + error_missing % picking.env._("resolution")
            )

        return {
            "labelLayout": label_layout,
            "printAddresses": "RECIPIENT_AND_CUSTOMER",
            "imageFileType": output_format,
            "imageResolution": image_resolution,
            "printPreview": False,
        }

    @classmethod
    def _request_access_token(cls, delivery_carrier):
        if not delivery_carrier.postlogistics_endpoint_url:
            raise UserError(
                delivery_carrier.env._(
                    "Missing Configuration\n\n"
                    "Please verify postlogistics endpoint url in:\n"
                    "Delivery Carrier (PostLogistics)."
                )
            )

        client_id = delivery_carrier.postlogistics_client_id
        client_secret = delivery_carrier.postlogistics_client_secret
        authentication_url = urllib.parse.urljoin(
            delivery_carrier.postlogistics_endpoint_url or "", AUTH_PATH
        )

        if not (client_id and client_secret):
            raise UserError(
                delivery_carrier.env._(
                    "Authorization Required\n\n"
                    "Please verify postlogistics client id and secret in:\n"
                    "Delivery Carrier (PostLogistics)."
                )
            )

        response = requests.post(
            url=authentication_url,
            headers={"content-type": "application/x-www-form-urlencoded"},
            data={
                "grant_type": "client_credentials",
                "client_id": client_id,
                "client_secret": client_secret,
                "scope": "WEDEC_BARCODE_READ",
            },
            timeout=60,
        )

        try:
            response.raise_for_status()
            json_response = response.json()
        except (
            JSONDecodeError,
            requests.exceptions.HTTPError,
        ) as error:
            raise UserError(
                delivery_carrier.env._(
                    "Postlogistics service is not accessible at the moment. Error code:"
                    " %s. "
                    "Please try again later." % (response.status_code or "None")
                )
            ) from error

        return json_response

    @classmethod
    def get_access_token(cls, picking_carrier):
        """Threadsafe access to token"""
        with cls._lock:
            now = datetime.now()

            if cls.access_token:
                # keep a safe margin on the expiration
                expiry = cls.access_token_expiry - timedelta(seconds=5)
                if now < expiry:
                    return cls.access_token

            response = cls._request_access_token(picking_carrier)
            cls.access_token = response.get("access_token", False)

            if not (cls.access_token):
                raise UserError(
                    picking_carrier.env._(
                        "Authorization Required\n\n"
                        "Please verify postlogistics client id and secret in:\n"
                        "Sale Orders > Configuration -> Sale Orders >"
                        " Shipping Methods > PostLogistics"
                    )
                )

            cls.access_token_expiry = now + timedelta(seconds=response["expires_in"])
            return cls.access_token

    def generate_label(self, picking, packages):
        """Generate a label for a picking

        :param picking: picking browse record
        :param user_lang: OpenERP language code
        :param packages: browse records of packages to filter on
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
        results = []
        picking_carrier = picking.carrier_id
        access_token = self.get_access_token(picking_carrier)

        # get options
        lang = self._get_language(picking.partner_id.lang)
        post_customer = picking.postlogistics_label_prepare_customer()
        recipient = picking.postlogistics_label_prepare_recipient()
        item_list = self._prepare_item_list(picking, recipient, packages)
        labelDefinition = self._prepare_label_definition(picking)
        frankingLicense = self._get_license(picking)

        for item in item_list:
            data = self._prepare_data(
                lang, frankingLicense, post_customer, labelDefinition, item
            )

            res = {"value": []}

            generate_label_url = urllib.parse.urljoin(
                picking_carrier.postlogistics_endpoint_url, GENERATE_LABEL_PATH
            )
            response = requests.post(
                url=generate_label_url,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "accept": "application/json",
                    "content-type": "application/json",
                },
                data=json.dumps(data),
                timeout=60,
            )

            if response.status_code != 200:
                res["success"] = False
                res["errors"] = response.content.decode("utf-8")
                _logger.warning(
                    "Shipping label could not be generated.\n"
                    "Request: {datas}\n"
                    "Response: {error}".format(
                        datas=json.dumps(data), error=res["errors"]
                    )
                )
                return [res]

            response_dict = json.loads(response.content.decode("utf-8"))

            if response_dict["item"].get("errors"):
                # If facing an error, top all operations and return the result
                res["success"] = False
                res["errors"] = []
                for error in response_dict["item"]["errors"]:
                    res["errors"] = picking.env._(
                        "Error code: %(code)s, Message: %(message)s"
                    ) % {
                        "code": error["code"],
                        "message": error["message"],
                    }
                results.append(res)
                return results

            output_format = self._get_output_format(picking).lower()
            file_type = output_format if output_format != "spdf" else "pdf"
            binary = base64.b64encode(bytes(response_dict["item"]["label"][0], "utf-8"))
            res["success"] = True
            res["value"].append(
                {
                    "item_id": item["itemID"],
                    "binary": binary,
                    "tracking_number": response_dict["item"]["identCode"],
                    "file_type": file_type,
                }
            )
            results.append(res)
        return results

    # These methods could be overridden in a custom module, thus if several
    # modules are installed but not chained properly, the last one will be used.
    # Meaning if you doesn't inherit from the last module, this module override
    # will not be used. This is a big issue in a modular environment, thus we
    # need to provide a better way to allow to override these methods by
    # implementing them in the picking model.

    @deprecated(
        "This method will be removed in version > 18.0. Please use \
`stock.picking::postlogistics_label_cash_on_delivery` instead."
    )
    def _cash_on_delivery(self, picking, package=None):
        # TODO: remove this method in versions > 18.0
        return picking.postlogistics_label_cash_on_delivery(package=package)

    @deprecated(
        "This method will be removed in version > 18.0. Please use \
`stock.picking::postlogistics_label_get_item_additional_data` instead."
    )
    def _get_item_additional_data(self, picking, package=None):
        # TODO: remove this method in versions > 18.0 and reimplement current
        #  behavior inside stock.picking::postlogistics_label_get_item_additional_data
        if package and not package.package_type_id:
            raise UserError(
                self.env._("The package %s must have a package type.") % package.name
            )
        result = picking.postlogistics_label_get_item_additional_data(package=package)
        packaging_codes = (
            package and package.package_type_id._get_shipper_package_code_list() or []
        )
        if set(packaging_codes) & {"BLN", "N"}:
            cod_attributes = picking.postlogistics_label_cash_on_delivery(
                package=package
            )
            result += cod_attributes
        return result

    @deprecated(
        "This method will be removed in version > 18.0. \
Please use global `sanitize_string` instead."
    )
    def _sanitize_string(self, value, mapping=None):
        # TODO: remove this method in versions > 18.0
        return sanitize_string(value, mapping)

    @deprecated(
        "This method will be removed in version > 18.0. Please use \
`stock.picking::postlogistics_label_prepare_attributes` instead."
    )
    def _prepare_attributes(
        self, picking, pack=None, pack_num=None, pack_total=None, pack_weight=None
    ):
        # TODO: remove this method in versions > 18.0
        return picking.postlogistics_label_prepare_attributes(
            pack=pack, pack_num=pack_num, pack_total=pack_total, pack_weight=pack_weight
        )

    @deprecated(
        "This method will be removed in version > 18.0. Please use \
`stock.picking::postlogistics_label_prepare_customer` instead."
    )
    def _prepare_customer(self, picking):
        # TODO: remove this method in versions > 18.0
        return picking.postlogistics_label_prepare_customer()

    @deprecated(
        "This method will be removed in version > 18.0. Please use \
`stock.picking::postlogistics_label_prepare_recipient` instead."
    )
    def _prepare_recipient(self, picking):
        # TODO: remove this method in versions > 18.0
        return picking.postlogistics_label_prepare_recipient()
