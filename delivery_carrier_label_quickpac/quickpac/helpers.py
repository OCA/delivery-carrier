# Copyright 2021 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import base64
import io
import re
from email.utils import parseaddr

import unidecode
from odoo import _
from odoo.exceptions import UserError
from PIL import Image
from quickpac import (
    Communication,
    Dimensions,
    GenerateLabelCustomer,
    GenerateLabelDefinition,
    GenerateLabelEnvelope,
    GenerateLabelFileInfos,
    Item,
    LabelData,
    LabelDataProvider,
    LabelDataProviderSending,
    Notification,
    Recipient,
    ServiceCodeAttributes,
)

_compile_itemid = re.compile(r'[^0-9A-Za-z+\-_]')
_compile_itemnum = re.compile(r'[^0-9]')


def _sanitize_string(string):
    """ Remove all non ascii char """
    return unidecode.unidecode(string)


def get_single_option(picking, option):
    """ Get an option from picking or from company """
    option = [
        opt.code for opt in picking.option_ids if opt.quickpac_type == option
    ]
    assert len(option) <= 1
    return option and option[0]


def get_label_layout(picking):
    label_layout = get_single_option(picking, 'label_layout')
    if not label_layout:
        company = picking.company_id
        label_layout = company.quickpac_label_layout.code
    return label_layout


def get_output_format(picking):
    output_format = get_single_option(picking, 'output_format')
    if not output_format:
        company = picking.company_id
        output_format = company.quickpac_output_format.code
    return output_format


def get_image_resolution(picking):
    resolution = get_single_option(picking, 'resolution')
    if not resolution:
        company = picking.company_id
        resolution = company.quickpac_resolution.code
    return resolution


def get_logo(picking):
    logo = get_single_option(picking, 'logo')
    if not logo:
        company = picking.company_id
        logo = company.quickpac_logo
    return logo


def generate_picking_itemid(picking, pack_no):
    """ Allowed characters are alphanumeric plus `+`, `-` and `_`
    Last `+` separates picking name and package number (if any)

    :param picking: a picking record
    :param pack_num: the current packing number
    :return string: itemid
    """
    name = _compile_itemid.sub('', picking.name)
    if pack_no:
        pack_no = _compile_itemid.sub('', pack_no)
    codes = [name, pack_no]
    return "+".join(c for c in codes if c)


def generate_tracking_number(picking, pack_num):
    """ Generate the tracking reference for the last 8 digits
    of tracking number of the label.

    2 first digits for a pack counter
    6 last digits for the picking name

    e.g. 03000042 for 3rd pack of picking OUT/19000042

    :param picking: a picking record
    :param pack_num: the current packing number
    :return string: the tracking number
    """
    picking_num = _compile_itemnum.sub('', picking.name)
    return '%02d%s' % (pack_num, picking_num[-6:].zfill(6))


def prepare_label_definition(picking):
    """ Define how the label will look like

    :param picking: a picking record
    :return: GenerateLabelDefinition
    """
    label_layout = get_label_layout(picking)
    output_format = get_output_format(picking)
    image_resolution = get_image_resolution(picking)

    error_missing = _(
        "You need to configure %s. You can set a default"
        "value in Settings/Configuration/Carriers/Quickpac."
        " You can also set it on delivery method or on the picking."
    )
    if not label_layout:
        raise UserError(
            _('Layout not set') + '\n' + error_missing % _("label layout")
        )
    if not output_format:
        raise UserError(
            _('Output format not set')
            + '\n'
            + error_missing % _("output format")
        )
    if not image_resolution:
        raise UserError(
            _('Resolution not set') + '\n' + error_missing % _("resolution")
        )

    label_definition = GenerateLabelDefinition(
        print_addresses="RecipientAndCustomer",
        image_file_type=output_format,
        image_resolution=image_resolution,
        print_preview=False,
        label_layout=label_layout,
    )
    return label_definition


def prepare_customer(picking, company):
    """ Define the Quickpac direct client

    :param picking: a picking record
    :param company: The company sending the goods
    :return: GenerateLabelCustomer
    """
    customer = GenerateLabelCustomer(
        name1=company.name,
        street=company.street,
        zip=company.zip,
        city=company.city,
    )
    logo = get_logo(picking)
    if logo:
        bytes_logo = base64.b64decode(logo.decode())
        logo_image = Image.open(io.BytesIO(bytes_logo))
        logo_format = logo_image.format
        customer.logo = logo.decode()
        customer.logo_format = logo_format
    return customer


def prepare_file_infos(picking, company):
    """ Define the sender informations

    :param picking: a picking record
    :param company: The company sending the goods
    :return: GenerateLabelFileInfos
    """
    customer = prepare_customer(picking, company)
    file_infos = GenerateLabelFileInfos(
        mode="Label",
        franking_license=company.quickpac_franking_license,
        customer=customer,
    )
    return file_infos


def prepare_recipient(picking):
    """ Create a Recipient for a partner from a picking

    :param picking: a picking record
    :return: Recipient
    """
    partner = picking.partner_id
    partner_name = partner.name or partner.parent_id.name
    email = parseaddr(partner.email)[1]
    recipient = Recipient(
        name1=_sanitize_string(partner.name),
        street=_sanitize_string(partner.street),
        zip=partner.zip,
        city=partner.city,
        e_mail=email or None,
    )

    if partner.country_id.code:
        recipient.country = partner.country_id.code.upper()
    if partner.street2:
        recipient.addressSuffix = _sanitize_string(partner.street2)

    if partner.parent_id and partner.parent_id.name != partner_name:
        recipient.name2 = _sanitize_string(partner.parent_id.name)
        recipient.personallyAddressed = False

    # Phone and / or mobile should only be displayed if instruction to
    # Notify delivery by telephone is set
    is_phone_required = [
        option for option in picking.option_ids if option.code == 'ZAW3213'
    ]
    if is_phone_required:
        phone = picking.delivery_phone or partner.phone
        if phone:
            recipient.phone = phone

        mobile = picking.delivery_mobile or partner.mobile
        if mobile:
            recipient.mobile = mobile

    return recipient


def prepare_attributes(picking, pack_counter=None, pack_total=None):
    """ Define specific attributes for a delivery

    :param picking: a picking record
    :param pack_counter: the current package index
    :param pack_total: the total packages number
    :return: ServiceCodeAttributes
    """
    dimensions = Dimensions(weight=picking.shipping_weight)
    attributes = ServiceCodeAttributes(przl=["2000"], dimensions=dimensions)
    return attributes


def prepare_notification(picking):
    """ Define how and who will be notified

    :param picking: a picking record
    :return: Notification
    """
    communication = Communication(item=picking.partner_id.email)
    notification = Notification(
        communication=communication,
        service="441",
        language=get_language(picking.partner_id.lang),
        type="EMAIL",
    )
    return notification


def prepare_items(picking, packages=None):
    """ Return a list of item made from the picking/packages

    :param picking: a picking record
    :param packages: a packages record
    :return: a list of Item
    """
    company = picking.company_id
    items = []
    pack_counter = 1

    def add_item(package=None, attributes=None):
        assert picking or package
        itemid = generate_picking_itemid(
            picking, package.name if package else picking.name
        )
        item_number = None
        if company.quickpac_tracking_format == 'picking_num':
            if not package:
                # start with 9 to garentee uniqueness and use 7 digits
                # of picking number
                picking_num = _compile_itemnum.sub('', picking.name)
                item_number = '9%s' % picking_num[-7:].zfill(7)
            else:
                item_number = generate_tracking_number(picking, pack_counter)

        recipient = prepare_recipient(picking)
        attributes = attributes or prepare_attributes(picking)
        notifications = prepare_notification(picking)
        item = Item(
            item_id=itemid,
            ident_code=item_number,
            recipient=recipient,
            attributes=attributes,
            notification=[notifications],
        )
        items.append(item)

    if not packages:
        add_item()

    pack_total = len(packages)
    for pack in packages:
        attributes = prepare_attributes(picking, pack_counter, pack_total)
        add_item(package=pack, attributes=attributes)
        pack_counter += 1

    return items


def prepare_data(picking, company, packages=None):
    """ Define packages data inside this shipment

    :param picking: The picking to process
    :param company: The company sending the goods
    :param packages: a packages record
    :return: LabelData
    """
    items = prepare_items(picking, packages)
    sending = LabelDataProviderSending(
        sending_id=company.quickpac_sending_id, item=items
    )
    provider = LabelDataProvider(sending=sending)
    data = LabelData(provider=provider)
    return data


def prepare_envelope(picking, company, packages=None):
    """ Define the main object that contains everything

    :param picking: The picking to process
    :param company: The company sending the goods
    :param packages: a packages record
    :return: GenerateLabelEnvelope
    """
    file_infos = prepare_file_infos(picking, company)
    label_definition = prepare_label_definition(picking)
    data = prepare_data(picking, company, packages)
    envelope = GenerateLabelEnvelope(
        label_definition=label_definition, file_infos=file_infos, data=data
    )
    return envelope


def get_language(lang, default_lang="de"):
    """ Return a language to iso format from odoo format.

    `iso_code` field in res.lang is not mandatory thus not always set.
    Use partner language if available, otherwise use english

    :param lang: the lang to map
    :param default_lang: the default lang
    :return: language code to use.
    """
    if not lang:
        lang = default_lang
    available_languages = ['de', 'en', 'fr', 'it']  # Given by API doc
    lang_code = lang.split('_')[0]
    if lang_code in available_languages:
        return lang_code
    return default_lang
