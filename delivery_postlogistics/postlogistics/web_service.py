# Copyright 2013-2019 Yannick Vaucher (Camptocamp SA)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
import json
import logging
import re
import threading
import urllib.parse
from datetime import datetime, timedelta
from io import BytesIO

from odoo import _, exceptions

import requests
from PIL import Image

_logger = logging.getLogger(__name__)

_compile_itemid = re.compile(r"[^0-9A-Za-z+\-_]")
_compile_itemnum = re.compile(r"[^0-9]")
AUTH_PATH = "/WEDECOAuth/token"
GENERATE_LABEL_PATH = "/api/barcode/v1/generateAddressLabel"


class PostlogisticsWebService(object):

    """ Connector with PostLogistics for labels using post.ch API

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
        """ Return a language to iso format from odoo format.

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

    def _prepare_recipient(self, picking):
        """ Create a ns0:Recipient as a dict from a partner

        :param partner: partner browse record
        :return a dict containing data for ns0:Recipient

        """
        partner = picking.partner_id
        partner_mobile = picking.delivery_mobile or partner.mobile
        partner_phone = picking.delivery_phone or partner.phone

        if partner.postlogistics_notification == "email" and not partner.email:
            raise exceptions.UserError(_("Email is required for notification."))
        elif partner.postlogistics_notification == "sms" and not partner_mobile:
            raise exceptions.UserError(
                _("Mobile number is required for sms notification.")
            )
        elif partner.postlogistics_notification == "phone" and not partner_phone:
            raise exceptions.UserError(
                _("Phone number is required for phone call notification.")
            )

        partner_name = partner.name or partner.parent_id.name
        recipient = {
            "name1": partner_name[:35],
            "street": partner.street[:35],
            "zip": partner.zip[:10],
            "city": partner.city[:35],
        }

        if partner.country_id.code:
            recipient["country"] = partner.country_id.code.upper()

        if partner.street2:
            recipient["addressSuffix"] = partner.street2[:35]

        company_partner_name = partner.commercial_company_name
        if company_partner_name and company_partner_name != partner_name:
            recipient["name2"] = partner.parent_id.name[:35]
            recipient["personallyAddressed"] = False

        # Phone and / or mobile should only be displayed if instruction to
        # Notify delivery by telephone is set
        if partner.postlogistics_notification == "email":
            recipient["email"] = partner.email
        elif partner.postlogistics_notification == "phone":
            recipient["phone"] = partner_phone
            if partner_mobile:
                recipient["mobile"] = partner_mobile
        elif partner.postlogistics_notification == "sms":
            recipient["mobile"] = partner_mobile

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
            "name1": partner.name,
            "street": partner.street,
            "zip": partner.zip,
            "city": partner.city,
            "country": partner.country_id.code,
            "domicilePostOffice": picking.carrier_id.postlogistics_office or None,
        }
        logo = picking.carrier_id.postlogistics_logo
        if logo:
            logo_image = Image.open(BytesIO(base64.b64decode(logo)))
            logo_format = logo_image.format
            customer["logo"] = logo.decode()
            customer["logoFormat"] = logo_format
        return customer

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
        """ Get the license

        Take it from carrier and if not defined get the first license.

        :return: license number
        """
        franking_license = picking.carrier_id.postlogistics_license_id
        return franking_license.number

    def _prepare_attributes(self, picking, pack=None, pack_num=None, pack_total=None):
        packaging = (
            pack
            and pack.packaging_id
            or picking.carrier_id.postlogistics_default_packaging_id
        )
        services = packaging._get_packaging_codes()

        total_weight = pack.shipping_weight if pack else picking.shipping_weight
        total_weight *= 1000

        if not services:
            raise exceptions.UserError(
                _("No Postlogistics packaging services found in this picking.")
            )

        # Activate phone notification ZAW3213
        # if phone call notification is set on partner
        if picking.partner_id.postlogistics_notification == "phone":
            services.append("ZAW3213")

        attributes = {
            "weight": int(total_weight),
        }

        # Remove the services if the delivery fixed date is not set
        if "ZAW3217" in services:
            if picking.delivery_fixed_date:
                attributes["deliveryDate"] = picking.delivery_fixed_date
            else:
                services.remove("ZAW3217")

        # parcelNo / parcelTotal cannot be used if service ZAW3218 is not activated
        if "ZAW3218" in services:
            if pack_total > 1:
                attributes.update(
                    {"parcelTotal": pack_total - 1, "parcelNo": pack_num - 1}
                )
            else:
                services.remove("ZAW3218")

        if "ZAW3219" in services and picking.delivery_place:
            attributes["deliveryPlace"] = picking.delivery_place
        if picking.carrier_id.postlogistics_proclima_logo:
            attributes["proClima"] = True
        else:
            attributes["proClima"] = False

        attributes["przl"] = services

        return attributes

    def _get_itemid(self, picking, pack_no):
        """ Allowed characters are alphanumeric plus `+`, `-` and `_`
        Last `+` separates picking name and package number (if any)

        :return string: itemid

        """
        name = _compile_itemid.sub("", picking.name)
        if not pack_no:
            return name

        pack_no = _compile_itemid.sub("", pack_no)
        codes = [name, pack_no]
        return "+".join(c for c in codes if c)

    def _cash_on_delivery(self, picking, package=None):
        if package:
            amount = package.postlogistics_cod_amount()
        else:
            amount = picking.postlogistics_cod_amount()
        amount = "{:.2f}".format(amount)
        return [{"Type": "NN_BETRAG", "Value": amount}]

    def _get_item_additional_data(self, picking, package=None):
        if package and not package.packaging_id:
            raise exceptions.UserError(
                _("The package %s must have a package type.") % package.name
            )

        result = []
        packaging_codes = package and package.packaging_id._get_packaging_codes() or []

        if set(packaging_codes) & {"BLN", "N"}:
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
        picking_num = _compile_itemnum.sub("", picking.name)
        return "%02d%s" % (pack_num, picking_num[-6:].zfill(6))

    def _prepare_item_list(self, picking, recipient, packages):
        """ Return a list of item made from the pickings """
        carrier = picking.carrier_id
        item_list = []
        pack_counter = 1

        def add_item(package=None):
            assert picking or package
            itemid = self._get_itemid(picking, package.name if package else None)
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
                    item_number = "9%s" % picking_num[-7:].zfill(7)
                else:
                    item_number = self._get_item_number(picking, pack_counter)
                item["itemNumber"] = item_number

            additional_data = self._get_item_additional_data(picking, package=package)
            if additional_data:
                item["additionalData"] = additional_data

            item_list.append(item)

        if not packages:
            attributes = self._prepare_attributes(picking)
            add_item()
            return item_list

        pack_total = len(packages)
        for pack in packages:
            attributes = self._prepare_attributes(
                picking, pack, pack_counter, pack_total
            )
            add_item(package=pack)
            pack_counter += 1
        return item_list

    def _prepare_label_definition(self, picking):
        error_missing = _(
            "You need to configure %s. You can set a default"
            " value in Inventory / Configuration / Delivery / Shipping Methods."
            " You can also set it on delivery method or on the picking."
        )
        label_layout = self._get_label_layout(picking)
        if not label_layout:
            raise exceptions.UserError(
                _("Layout not set") + "\n" + error_missing % _("label layout")
            )

        output_format = self._get_output_format(picking)
        if not output_format:
            raise exceptions.UserError(
                _("Output format not set") + "\n" + error_missing % _("output format")
            )

        image_resolution = self._get_image_resolution(picking)
        if not image_resolution:
            raise exceptions.UserError(
                _("Resolution not set") + "\n" + error_missing % _("resolution")
            )

        return {
            "labelLayout": label_layout,
            "printAddresses": "RECIPIENT_AND_CUSTOMER",
            "imageFileType": output_format,
            "imageResolution": image_resolution,
            "printPreview": False,
        }

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

    @classmethod
    def _request_access_token(cls, delivery_carrier):
        if not delivery_carrier.postlogistics_endpoint_url:
            raise exceptions.UserError(
                _(
                    "Missing Configuration\n\n"
                    "Please verify postlogistics endpoint url in:\n"
                    "Delivery Carrier (Postlogistics)."
                )
            )

        client_id = delivery_carrier.postlogistics_client_id
        client_secret = delivery_carrier.postlogistics_client_secret
        authentication_url = urllib.parse.urljoin(
            delivery_carrier.postlogistics_endpoint_url or "", AUTH_PATH
        )

        if not (client_id and client_secret):
            raise exceptions.UserError(
                _(
                    "Authorization Required\n\n"
                    "Please verify postlogistics client id and secret in:\n"
                    "Delivery Carrier (Postlogistics)."
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
        return response.json()

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
            cls.access_token = response["access_token"]

            if not (cls.access_token):
                raise exceptions.UserError(
                    _(
                        "Authorization Required\n\n"
                        "Please verify postlogistics client id and secret in:\n"
                        "Configuration -> Postlogistics"
                    )
                )

            cls.access_token_expiry = now + timedelta(seconds=response["expires_in"])
            return cls.access_token

    def generate_label(self, picking, packages):
        """ Generate a label for a picking

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
        post_customer = self._prepare_customer(picking)
        recipient = self._prepare_recipient(picking)
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
                    "Authorization": "Bearer %s" % access_token,
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
                    "Request: %s\n"
                    "Response: %s" % (json.dumps(data), res["errors"])
                )
                return [res]

            response_dict = json.loads(response.content.decode("utf-8"))

            if response_dict["item"].get("errors"):
                # If facing an error, top all operations and return the result
                res["success"] = False
                res["errors"] = []
                for error in response_dict["item"]["errors"]:
                    res["errors"] = _("Error code: %s, Message: %s") % (
                        error["code"],
                        error["message"],
                    )
                results.append(res)
                return results

            output_format = self._get_output_format(picking).lower()
            file_type = output_format if output_format != "spdf" else "pdf"
            binary = base64.b64encode(bytes(response_dict["item"]["label"][0], "utf-8"))
            res["success"] = True
            res["value"].append(
                {
                    "item_id": item_list[0]["itemID"],
                    "binary": binary,
                    "tracking_number": response_dict["item"]["identCode"],
                    "file_type": file_type,
                }
            )
            results.append(res)
        return results
