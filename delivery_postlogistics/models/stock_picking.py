# Copyright 2013 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import base64
import logging
from io import BytesIO
from operator import attrgetter

import lxml.html
from PIL import Image

from odoo import api, fields, models
from odoo.exceptions import UserError

from ..postlogistics.web_service import PostlogisticsWebService, sanitize_string

_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _inherit = "stock.picking"

    delivery_fixed_date = fields.Date(
        "Fixed delivery date", help="Specific delivery date (ZAW3217)"
    )

    # TODO: consider refactoring these fields using a partner relation instead
    delivery_place = fields.Char(help="For Deposit item service (ZAW3219)")
    delivery_phone = fields.Char(
        "Phone", help="For notify delivery by telephone (ZAW3213)"
    )
    delivery_mobile = fields.Char(
        "Mobile", help="For notify delivery by telephone (ZAW3213)"
    )

    def _get_packages_from_picking(self):
        # As CI doesn't allow warnings, we need to log as info here
        # (deprecated decorator is unhelpfull).
        _logger.info(
            "This method will be removed in version 18.0. \
Please use _get_quant_packages_from_picking instead."
        )
        # TODO: remove this method in version > 18.0
        return self._get_quant_packages_from_picking()

    def _get_quant_packages_from_picking(self):
        """Get all the quant packages from the picking"""
        self.ensure_one()
        operations = self.env["stock.move.line"].search(
            [
                "|",
                ("package_id", "!=", False),
                ("result_package_id", "!=", False),
                ("picking_id", "=", self.id),
            ]
        )
        package_ids = set()
        for operation in operations:
            # Take the destination package. If empty, the package is
            # moved so take the source one.
            package_ids.add(operation.result_package_id.id or operation.package_id.id)

        return self.env["stock.quant.package"].browse(package_ids)

    def attach_shipping_label(self, label):
        """Attach a label returned by generate_shipping_labels to a picking"""
        if self.delivery_type != "postlogistics":
            return super().attach_shipping_label(label)
        self.ensure_one()
        data = self.get_shipping_label_values(label)
        # remove `default_type` set for stock_picking
        # as it would try to define default value of attachement
        if self.env.context.get("default_type"):
            new_ctx = self.env.context.copy()
            new_ctx.pop("default_type")
            self = self.with_context(new_ctx)  # pylint: disable=context-overridden
        return self.env["shipping.label"].create(data)

    def postlogistics_cod_amount(self):
        """Return the PostLogistics Cash on Delivery amount of a picking

        If the picking delivers the whole sales order, we use the total
        amount of the sales order.

        Otherwise, we don't know the value of each picking so we raise
        an error.  The user has to create packages with the cash on
        delivery price on each package.
        """
        self.ensure_one()
        order = self.sale_id
        if not order:
            return 0.0
        if len(order) > 1:
            raise UserError(
                self.env._(
                    "The cash on delivery amount must be manually specified "
                    "on the packages when a package contains products "
                    "from different sales orders."
                )
            )
        # check if the package delivers the whole sales order
        if len(order.picking_ids) > 1:
            raise UserError(
                self.env._(
                    "The cash on delivery amount must be manually specified "
                    "on the packages when a sales order is delivered "
                    "in several delivery orders."
                )
            )
        return order.amount_total

    def info_from_label(self, label, zpl_patch_string=False, package_id=False):
        tracking_number = label["tracking_number"]
        data = base64.b64decode(label["binary"])

        # Apply patch for zpl file
        if label["file_type"] == "zpl2" and zpl_patch_string:
            data = base64.b64encode(
                base64.b64decode(data)
                .decode("cp437")
                .replace("^XA", zpl_patch_string)
                .encode("utf-8")
            )
        return {
            "file": data,
            "file_type": label["file_type"],
            "name": tracking_number + "." + label["file_type"],
            "package_id": package_id,
        }

    def write_tracking_number_label(self, label_result, packages):
        """
        If there are no pack defined, write tracking_number on picking
        otherwise, write it on parcel_tracking field of each pack.
        Note we can receive multiple labels for a same package
        """
        zpl_patch_string = self.carrier_id.zpl_patch_string

        labels = []

        # It could happen that no successful label has been returned by the API
        if not label_result:
            return labels

        if not packages:
            label = label_result[0]["value"][0]
            self.carrier_tracking_ref = label["tracking_number"]
            labels.append(self.info_from_label(label, zpl_patch_string))

        tracking_refs = []
        for package in packages:
            tracking_numbers = []
            for label in label_result:
                for label_value in label["value"]:
                    if package.name in label_value["item_id"].split("+")[-1]:
                        tracking_numbers.append(label_value["tracking_number"])
                        labels.append(
                            self.info_from_label(
                                label_value, zpl_patch_string, package_id=package.id
                            )
                        )
            package.parcel_tracking = "; ".join(tracking_numbers)
            tracking_refs += tracking_numbers

        existing_tracking_ref = (
            self.carrier_tracking_ref and self.carrier_tracking_ref.split("; ") or []
        )
        self.carrier_tracking_ref = "; ".join(existing_tracking_ref + tracking_refs)
        return labels

    def _generate_postlogistics_label(
        self, webservice_class=None, packages=None, skip_attach_file=False
    ):
        """Generate labels and write tracking numbers received"""
        self.ensure_one()
        user = self.env.user
        company = user.company_id
        if webservice_class is None:
            webservice_class = PostlogisticsWebService

        if packages is None:
            packages = self._get_quant_packages_from_picking()
        packages = packages.sorted(key=attrgetter("name"))

        web_service = webservice_class(company)

        # Do not generate label for packages that are already done
        packages = packages.filtered(lambda p: not p.parcel_tracking)

        label_results = web_service.generate_label(self, packages)

        failed_label_results = [label for label in label_results if "errors" in label]
        if failed_label_results:
            # Shipments are invoiced by postlogistics only when the label is scanned
            # for the first time.
            # Therefore, we don't have to attach labels, we can generate a new one
            # each time we try to confirm a picking.
            # Raise and exception, and let odoo rollback the transaction.
            error_message = "\n".join(
                self._cleanup_error_message(label["errors"])
                for label in failed_label_results
            )
            raise UserError(self.env._("PostLogistics error:") + "\n\n" + error_message)

        labels = self.write_tracking_number_label(label_results, packages)

        if not skip_attach_file:
            for label in labels:
                self.attach_shipping_label(label)

        return labels

    @api.model
    def _cleanup_error_message(self, error_message):
        """Cleanup HTML error message to be readable by users."""
        texts_no_html = lxml.html.fromstring(error_message).text_content()
        texts = [text for text in texts_no_html.split("\n") if text]
        return "\n".join(texts)

    def generate_postlogistics_shipping_labels(self, packages=None):
        """Add label generation for PostLogistics"""
        self.ensure_one()
        return self._generate_postlogistics_label(packages=packages)

    def action_generate_carrier_label(self):
        self.ensure_one()
        if not self.carrier_id:
            raise UserError(self.env._("Please, set a carrier."))
        self.env["delivery.carrier"].postlogistics_send_shipping(self)

    #
    # Postlogistics specific methods allowing proper override
    #

    def get_package_number_hook(self, package):
        """Hook method to customize the package number retrieval"""
        return None

    def get_recipient_partner_hook(self):
        """Hook method to customize the partner retrieval"""
        self.ensure_one()
        if self.picking_type_id.code != "outgoing":
            return (
                self.location_dest_id.company_id.partner_id
                or self.env.user.company_id.partner_id
            )
        return self.partner_id

    def postlogistics_label_prepare_attributes(
        self, pack=None, pack_num=None, pack_total=None, pack_weight=None
    ):
        """This method aims to prepare a dictionary of attributes to be sent
        to the PostLogistics API"""
        self.ensure_one()
        package_type = (
            pack
            and pack.package_type_id
            or self.carrier_id.postlogistics_default_package_type_id
        )
        if not package_type:
            raise UserError(
                self.env._(
                    "No package type found either for the package "
                    f"or for the {self.carrier_id.name} delivery method."
                )
            )
        package_codes = package_type._get_shipper_package_code_list()

        if pack_weight:
            total_weight = pack_weight
        else:
            total_weight = pack.shipping_weight if pack else self.shipping_weight
        total_weight *= 1000

        if not package_codes:
            raise UserError(
                self.env._(
                    "No PostLogistics packaging services found "
                    "in package type {package_type_name}, for picking {picking_name}."
                ).format(package_type_name=package_type.name, picking_name=self.name)
            )

        # Activate phone notification ZAW3213
        # if phone call notification is set on partner
        if self.partner_id.postlogistics_notification == "phone":
            package_codes.append("ZAW3213")

        attributes = {
            "weight": int(total_weight),
        }

        # Remove the services if the delivery fixed date is not set
        if "ZAW3217" in package_codes:
            if self.delivery_fixed_date:
                attributes["deliveryDate"] = self.delivery_fixed_date
            else:
                package_codes.remove("ZAW3217")

        # parcelNo / parcelTotal cannot be used if service ZAW3218 is not activated
        if "ZAW3218" in package_codes:
            if pack_total > 1:
                attributes.update(
                    {"parcelTotal": pack_total - 1, "parcelNo": pack_num - 1}
                )
            else:
                package_codes.remove("ZAW3218")

        if "ZAW3219" in package_codes and self.delivery_place:
            attributes["deliveryPlace"] = self.delivery_place
        if self.carrier_id.postlogistics_proclima_logo:
            attributes["proClima"] = True
        else:
            attributes["proClima"] = False

        attributes["przl"] = package_codes

        return attributes

    def postlogistics_label_prepare_customer(self):
        """Create a ns0:Customer as a dict from picking

        This is the PostLogistics Customer, thus the sender

        :param picking: picking browse record
        :return a dict containing data for ns0:Customer

        """
        self.ensure_one()
        company = self.company_id
        partner = company.partner_id
        if self.picking_type_id.code != "outgoing":
            partner = self.partner_id

        partner_name = partner.name or partner.parent_id.name
        if not partner_name:
            raise UserError(self.env._("Customer name is required."))
        customer = {
            "name1": sanitize_string(partner_name)[:25],
            "street": sanitize_string(partner.street)[:25],
            "zip": sanitize_string(partner.zip)[:10],
            "city": sanitize_string(partner.city)[:25],
            "country": partner.country_id.code,
            "domicilePostOffice": self.carrier_id.postlogistics_office or None,
        }
        logo = self.carrier_id.postlogistics_logo
        if logo:
            logo_image = Image.open(BytesIO(base64.b64decode(logo)))
            logo_format = logo_image.format
            customer["logo"] = logo.decode()
            customer["logoFormat"] = logo_format
        return customer

    def postlogistics_label_prepare_recipient(self, sanitize_mapping=None):
        """Create a ns0:Recipient as a dict from a partner

        :param partner: partner browse record
        :return a dict containing data for ns0:Recipient

        """
        partner = self.get_recipient_partner_hook()

        partner_mobile = sanitize_string(
            self.delivery_mobile or partner.mobile, sanitize_mapping
        )
        partner_phone = sanitize_string(
            self.delivery_phone or partner.phone, sanitize_mapping
        )

        if partner.postlogistics_notification == "email" and not partner.email:
            raise UserError(self.env._("Email is required for notification."))
        elif partner.postlogistics_notification == "sms" and not partner_mobile:
            raise UserError(
                self.env._("Mobile number is required for sms notification.")
            )
        elif partner.postlogistics_notification == "phone" and not partner_phone:
            raise UserError(
                self.env._("Phone number is required for phone call notification.")
            )

        if not partner.street:
            raise UserError(self.env._("Partner street is required."))

        if not partner.name and not partner.parent_id.name:
            raise UserError(self.env._("Partner name is required."))

        if not partner.zip:
            raise UserError(self.env._("Partner zip is required."))

        if not partner.city:
            raise UserError(self.env._("Partner city is required."))

        partner_name = partner.name or partner.parent_id.name
        sanitized_partner_name = sanitize_string(partner_name, sanitize_mapping)
        partner_street = sanitize_string(partner.street, sanitize_mapping)
        partner_zip = sanitize_string(partner.zip, sanitize_mapping)
        partner_city = sanitize_string(partner.city, sanitize_mapping)
        recipient = {
            "name1": sanitized_partner_name[:35],
            "street": partner_street[:35],
            "zip": partner_zip[:10],
            "city": partner_city[:35],
        }

        if partner.country_id.code:
            country_code = sanitize_string(
                partner.country_id.code.upper(), sanitize_mapping
            )
            recipient["country"] = country_code

        if partner.street2:
            # addressSuffix is shown before street on label
            recipient["addressSuffix"] = recipient["street"]
            recipient["street"] = sanitize_string(
                partner.street2[:35], sanitize_mapping
            )

        company_partner_name = partner.commercial_company_name
        if company_partner_name and company_partner_name != partner_name:
            parent_name = sanitize_string(partner.parent_id.name, sanitize_mapping)
            recipient["name2"] = parent_name[:35]
            recipient["personallyAddressed"] = False

        # Phone and / or mobile should only be displayed if instruction to
        # Notify delivery by telephone is set
        if partner.postlogistics_notification == "email":
            recipient["email"] = sanitize_string(partner.email, sanitize_mapping)
        elif partner.postlogistics_notification == "phone":
            recipient["phone"] = sanitize_string(partner_phone, sanitize_mapping)
            if partner_mobile:
                recipient["mobile"] = partner_mobile
        elif partner.postlogistics_notification == "sms":
            recipient["mobile"] = partner_mobile

        return recipient

    def postlogistics_label_cash_on_delivery(self, package=None):
        amount = (package or self).postlogistics_cod_amount()
        amount = f"{amount:.2f}"
        return [{"Type": "NN_BETRAG", "Value": amount}]

    def postlogistics_label_get_item_additional_data(self, package=None):
        return []
