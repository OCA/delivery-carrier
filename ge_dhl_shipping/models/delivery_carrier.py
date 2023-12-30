import binascii
import json
import logging

from odoo import _, fields, models
from odoo.exceptions import ValidationError

from .dhl_request import DhlRequest

_logger = logging.getLogger(__name__)


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    delivery_type = fields.Selection(
        selection_add=[("dhl_parcel_de_provider", "DHL Parcel DE")],
        ondelete={"dhl_parcel_de_provider": "set default"},
    )

    dhl_parcel_de_provider_package_id = fields.Many2one(
        "stock.package.type", string="Package Info", help="Default Package"
    )
    dhl_weight_uom = fields.Selection(
        [("kg", "KG"), ("g", "G")],
        string="Weight UOM",
        help="Weight UOM of the Shipment",
    )
    dhl_services_name = fields.Selection(
        [
            ("V01PAK", "V01PAK-DHL PAKET"),
            ("V53WPAK", "V53WPAK-DHL PAKET International"),
            ("V54EPAK", "V54EPAK-DHL Europaket"),
            ("V62WP", "V62WP - DHL Warenpost"),
            ("V66WPI", "V66WPI - Warenpost International"),
        ],
        string="Product Name",
        help="Shipping Services those are accepted by DHL.",
    )
    dhl_account_no = fields.Char(
        string="DHL Account Number",
        help=(
            "The Account(EKP) number sent to you by DHL "
            "and it must be maximum 10 digit allow."
        ),
    )
    dhl_procedure_no = fields.Char(
        string="DHL Procedure Number",
        help=(
            "The Procedure refers to DHL products that are "
            "used for shipping and max length is 2 digit."
        ),
    )
    dhl_participation_no = fields.Char(
        string="DHL Participation Number",
        help=(
            "Participation number referred to as Partner ID in the web service."
            "The participation is 2 numerical digits from 00 to 99 "
            "or alphanumerical digits from AA to ZZ."
        ),
    )

    def check_address_details(self, address_id, required_fields):
        """
        check the address of Shipper and Recipient
        param : address_id: res.partner, required_fields:
        ['zip', 'city', 'country_id', 'street']
        return: missing address message
        """

        res = [field for field in required_fields if not address_id[field]]
        if res:
            return "Missing Values For Address :\n %s" % ", ".join(res).replace(
                "_id", ""
            )

    def dhl_parcel_de_provider_rate_shipment(self, order):
        """
        This method is used for get rate of shipment
        param : order : sale.order
        return: 'success': False : 'error message' : True
        return: 'success': True : 'error_message': False
        """
        # Shipper and Recipient Address
        shipper_address_id = order.warehouse_id.partner_id
        recipient_address_id = order.partner_shipping_id

        shipper_address_error = self.check_address_details(
            shipper_address_id, ["zip", "city", "country_id", "street"]
        )
        recipient_address_error = self.check_address_details(
            recipient_address_id, ["zip", "city", "country_id", "street"]
        )
        sum(
            (line.product_id.weight * line.product_uom_qty) for line in order.order_line
        ) or 0.0

        product_weight = order.order_line.filtered(
            lambda x: not x.is_delivery
            and x.product_id.type == "product"
            and x.product_id.weight <= 0
        )
        product_name = ", ".join(product_weight.mapped("product_id").mapped("name"))

        if shipper_address_error or recipient_address_error or product_name:
            return {
                "success": False,
                "price": 0.0,
                "error_message": "%(shipper)s %(receipient)s  %(extra)s "
                % {
                    "shipper": "Shipper Address : %s \n" % (shipper_address_error)
                    if shipper_address_error
                    else "",
                    "receipient": "Recipient Address : %s \n"
                    % (recipient_address_error)
                    if recipient_address_error
                    else "",
                    "extra": "product weight is not available : %s" % (product_name)
                    if product_name
                    else "",
                },
                "warning_message": False,
            }
        return {
            "success": True,
            "price": 0.0,
            "error_message": False,
            "warning_message": False,
        }

    def dhl_parcel_de_provider_retrive_package_info(self, picking):
        shipper_address_id = (
            picking.picking_type_id
            and picking.picking_type_id.warehouse_id
            and picking.picking_type_id.warehouse_id.partner_id
        )
        recipient_address_id = picking.partner_id
        sender_zip = shipper_address_id.zip or ""
        sender_city = shipper_address_id.city or ""
        sender_country_code = (
            shipper_address_id.country_id
            and shipper_address_id.country_id.code_alpha3
            or ""
        )
        sender_street = shipper_address_id.street or ""
        sender_phone = shipper_address_id.phone or ""
        sender_email = shipper_address_id.email or ""

        receiver_zip = recipient_address_id.zip or ""
        receiver_city = recipient_address_id.city or ""
        receiver_country_code = (
            recipient_address_id.country_id
            and recipient_address_id.country_id.code_alpha3
            or ""
        )
        receiver_street = recipient_address_id.street or ""
        receiver_phone = recipient_address_id.phone or ""
        receiver_email = recipient_address_id.email or ""
        billingNumber = (
            self.dhl_account_no + self.dhl_procedure_no + self.dhl_participation_no
        )

        package_data = {
            "product": self.dhl_services_name,
            "billingNumber": billingNumber,
            "refNo": picking.name or "",
            "shipper": {
                "name1": shipper_address_id.name,
                "addressStreet": sender_street,
                "postalCode": sender_zip,
                "city": sender_city,
                "country": sender_country_code,
                "email": sender_email,
                "phone": sender_phone,
            },
            "consignee": {
                "name1": recipient_address_id.name,
                "addressStreet": receiver_street,
                "postalCode": receiver_zip,
                "city": receiver_city,
                "country": receiver_country_code,
                "email": receiver_email,
                "phone": receiver_phone,
            },
        }
        return package_data

    def create_dhl_de_package_dict(self, height, length, width, weight):
        return {
            "details": {
                "dim": {
                    "uom": "mm",
                    "height": height,
                    "length": length,
                    "width": width,
                },
                "weight": {"uom": self.dhl_weight_uom, "value": int(weight)},
            }
        }

    def dhl_parcel_de_provider_packages(self, picking):
        package_list = []
        weight_bulk = picking.weight_bulk
        package_ids = picking.package_ids
        for package_id in package_ids:
            height = (
                package_id.package_type_id and package_id.package_type_id.height or 0
            )
            width = package_id.package_type_id and package_id.package_type_id.width or 0
            length = (
                package_id.package_type_id
                and package_id.package_type_id.packaging_length
                or 0
            )
            weight = package_id.shipping_weight
            package_data = self.create_dhl_de_package_dict(
                height, length, width, weight
            )
            request_data = self.dhl_parcel_de_provider_retrive_package_info(picking)
            package_data.update(request_data)
            package_list.append(package_data)
        if weight_bulk:
            height = (
                self.dhl_parcel_de_provider_package_id
                and self.dhl_parcel_de_provider_package_id.height
                or 0
            )
            width = (
                self.dhl_parcel_de_provider_package_id
                and self.dhl_parcel_de_provider_package_id.width
                or 0
            )
            length = (
                self.dhl_parcel_de_provider_package_id
                and self.dhl_parcel_de_provider_package_id.packaging_length
                or 0
            )
            weight = weight_bulk
            package_data = self.create_dhl_de_package_dict(
                height, length, width, weight
            )
            request_data = self.dhl_parcel_de_provider_retrive_package_info(picking)
            package_data.update(request_data)
            package_list.append(package_data)
        return package_list

    def dhl_parcel_de_provider_send_shipping(self, picking):
        shipper_address_id = (
            picking.picking_type_id
            and picking.picking_type_id.warehouse_id
            and picking.picking_type_id.warehouse_id.partner_id
        )
        recipient_address_id = picking.partner_id
        shipper_address_error = self.check_address_details(
            shipper_address_id, ["zip", "city", "country_id", "street"]
        )
        recipient_address_error = self.check_address_details(
            recipient_address_id, ["zip", "city", "country_id", "street"]
        )
        if (
            shipper_address_error
            or recipient_address_error
            or not picking.shipping_weight
        ):
            raise ValidationError(
                _("%(first)s %(second)s  %(third)s ")
                % {
                    "first": "Shipper Address : %s \n" % (shipper_address_error)
                    if shipper_address_error
                    else "",
                    "second": "Recipient Address : %s \n" % (recipient_address_error)
                    if recipient_address_error
                    else "",
                    "third": "Shipping weight is missing!"
                    if not picking.shipping_weight
                    else "",
                }
            )
        packages = self.dhl_parcel_de_provider_packages(picking)
        request_data = json.dumps({"shipments": packages})

        dhl_request = DhlRequest(self, picking)

        try:
            response_data = dhl_request._send_api_request(
                url=dhl_request.url,
                data=request_data,
                auth=True,
                method="POST",
                content_type="application/json",
            )
            response_data = json.loads(response_data)
            response_status = True
            final_tracking_number = []
            if (
                response_status
                and response_data.get("status")
                and response_data.get("status").get("statusCode") in [200]
            ):
                for package_id in response_data.get("items"):
                    tracking_number = package_id.get("shipmentNo")
                    label_data = package_id.get("label").get("b64")
                    binary_data = binascii.a2b_base64(str(label_data))
                    message = _(
                        "Label created!<br/> <b>Shipping  Number : </b>%s<br/>"
                    ) % (tracking_number,)
                    picking.message_post(
                        body=message,
                        attachments=[
                            ("Label-%s.%s" % (tracking_number, "pdf"), binary_data)
                        ],
                    )
                    final_tracking_number.append(tracking_number)
                shipping_data = {
                    "exact_price": 0.0,
                    "tracking_number": ",".join(final_tracking_number),
                }
                shipping_data = [shipping_data]
                return shipping_data
            else:
                raise ValidationError(response_data)
        except Exception as e:
            raise ValidationError(e) from e

    def dhl_parcel_de_provider_cancel_shipment(self, picking):
        raise ValidationError(_("Cancel Service not provide by DHL Parcel"))

    def dhl_parcel_de_provider_get_tracking_link(self, picking):
        if self.company_id and self.company_id.dhl_tracking_url:
            return self.company_id.dhl_tracking_url
        else:
            raise ValidationError(_("Please Set Tracking URL In Company"))
