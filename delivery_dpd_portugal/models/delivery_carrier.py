# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

import requests

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)

TEST_BASE_URL = "https://qabusiness.dpd.pt/api/v1/pt"
PROD_BASE_URL = "https://business.dpd.pt/api/v1/pt"


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    delivery_type = fields.Selection(
        selection_add=[("dpd_pt", "DPD Portugal")],
        ondelete={"dpd_pt": "set default"},
    )

    # DPD Portugal API Configuration
    dpd_portugal_service_type = fields.Selection(
        [
            ("standard", "Standard"),
            ("express", "Express"),
            ("economy", "Economy"),
        ],
        string="Service Type",
        default="standard",
        help="DPD Portugal service type",
    )
    dpd_portugal_label_format = fields.Selection(
        [("PDF", "PDF"), ("ZPL", "ZPL")],
        string="Label Format",
        default="PDF",
        help="Format for shipping labels",
    )
    dpd_portugal_default_package_type_id = fields.Many2one(
        "stock.package.type",
        string="Default Package Type",
        help="Default package type for DPD Portugal shipments",
    )
    dpd_portugal_package_weight_unit = fields.Selection(
        [("KG", "Kilograms"), ("LB", "Pounds")],
        string="Package Weight Unit",
        default="KG",
        help="Weight unit for packages",
    )
    dpd_portugal_package_dimension_unit = fields.Selection(
        [("CM", "Centimeters"), ("IN", "Inches")],
        string="Package Dimension Unit",
        default="CM",
        help="Dimension unit for packages",
    )

    # DPD Portugal Additional Services
    dpd_portugal_cod_enabled = fields.Boolean(
        string="Enable COD", help="Enable cash on delivery service"
    )
    dpd_portugal_insurance_enabled = fields.Boolean(
        string="Enable Insurance", help="Enable shipping insurance"
    )
    dpd_portugal_insurance_amount = fields.Float(
        string="Insurance Amount",
        help="Default insurance amount for shipments",
    )
    dpd_portugal_saturday_delivery = fields.Boolean(
        string="Saturday Delivery", help="Enable Saturday delivery service"
    )
    dpd_portugal_predict_enabled = fields.Boolean(
        string="Predict Service", help="Enable DPD Predict service"
    )

    # DPD Portugal Address & Contact Options
    dpd_portugal_hide_recipient_phone = fields.Boolean(
        string="Hide Recipient Phone",
        help="Hide recipient phone number from shipping label",
    )
    dpd_portugal_hide_recipient_email = fields.Boolean(
        string="Hide Recipient Email",
        help="Hide recipient email from shipping label",
    )
    dpd_portugal_send_label_email = fields.Boolean(
        string="Send Label by Email",
        help="Automatically send shipping label by email",
    )

    @api.depends("delivery_type")
    def _compute_can_generate_return(self):
        """Compute if carrier can generate return shipments."""
        result = super()._compute_can_generate_return()
        for carrier in self:
            if carrier.delivery_type == "dpd_pt":
                carrier.can_generate_return = True
        return result

    @api.depends("delivery_type", "dpd_portugal_insurance_enabled")
    def _compute_supports_shipping_insurance(self):
        """Compute if carrier supports shipping insurance."""
        result = super()._compute_supports_shipping_insurance()
        for carrier in self:
            if carrier.delivery_type == "dpd_pt":
                carrier.supports_shipping_insurance = (
                    carrier.dpd_portugal_insurance_enabled
                )
        return result

    def dpd_pt_rate_shipment(self, order):
        """Get shipping rates from DPD Portugal."""
        shipment_data = self._prepare_dpd_pt_shipment_data(order)
        try:
            rate_response = self._dpd_pt_request_with_account(
                "shipment/rate", shipment_data, order
            ).json()
        except Exception as e:
            return {
                "success": False,
                "price": 0.0,
                "error_message": self.env._(
                    "Rate calculation failed: %(error)s",
                    error=str(e),
                ),
                "warning_message": False,
            }

        if "price" in rate_response:
            return {
                "success": True,
                "price": rate_response["price"],
                "error_message": False,
                "warning_message": False,
            }
        else:
            return {
                "success": False,
                "price": 0.0,
                "error_message": self.env._(
                    "Unable to calculate rate: %(message)s",
                    message=rate_response.get("message", "Unknown error"),
                ),
                "warning_message": False,
            }

    def dpd_pt_send_shipping(self, pickings):
        """Send shipment to DPD Portugal and generate labels."""
        result = []
        for picking in pickings:
            # Validate picking data
            self._validate_dpd_pt_picking(picking)

            # Prepare shipment data
            shipment_data = self._prepare_dpd_pt_shipment_data(picking)

            # Create shipment using account-based request
            shipment_response = self._dpd_pt_request_with_account(
                "shipment/create", shipment_data, picking
            ).json()

            if shipment_response.get("success", False):
                # Update picking with tracking info
                tracking_number = shipment_response["tracking_number"]
                picking.carrier_tracking_ref = tracking_number

                # Get label using account
                label_response = self._dpd_pt_request_with_account(
                    f"shipment/label/{tracking_number}",
                    {"format": self.dpd_portugal_label_format},
                    picking,
                )
                label_content = label_response.content

                # Post message with label attachment
                label_name = (
                    f"DPD_Portugal_Label_{tracking_number}"
                    f".{self.dpd_portugal_label_format.lower()}"
                )
                message = picking.message_post(
                    body=self.env._("DPD Portugal label generated"),
                    attachments=[(label_name, label_content)],
                )

                # Send email if enabled
                if (
                    self.dpd_portugal_send_label_email
                    and picking.partner_id.email
                    and message.attachment_ids
                ):
                    template = self.env.ref(
                        "delivery_dpd_portugal.email_template_dpd_label",
                        raise_if_not_found=False,
                    )
                    if template:
                        template.send_mail(
                            picking.id,
                            force_send=True,
                            email_values={
                                "attachment_ids": [(4, message.attachment_ids[0].id)],
                                "email_to": picking.partner_id.email,
                            },
                        )

                result.append(
                    {
                        "exact_price": shipment_response.get("price", 0.0),
                        "tracking_number": shipment_response["tracking_number"],
                    }
                )
            else:
                raise UserError(
                    self.env._(
                        "Failed to create shipment: %(message)s",
                        message=shipment_response.get("message", "Unknown error"),
                    )
                )

        return result

    def dpd_pt_get_tracking_link(self, picking):
        """Return DPD Portugal tracking link for the given picking.

        :param picking: stock.picking record
        :return: tracking URL or False
        """
        if picking.carrier_tracking_ref:
            return f"https://www.dpd.pt/rastreamento?parcelNumber={picking.carrier_tracking_ref}"
        return False

    def dpd_pt_tracking_state_update(self, picking):
        """Update tracking state from DPD Portugal."""
        tracking_data = self._dpd_pt_request_with_account(
            f"shipment/track/{picking.carrier_tracking_ref}", {}, picking
        ).json()

        if "status" in tracking_data:
            # Update picking tracking state
            picking.tracking_state = tracking_data["status"]
            tracking_vals = {
                "tracking_number": picking.carrier_tracking_ref,
                "state": tracking_data["status"],
                "description": tracking_data.get("description", ""),
                "date": fields.Datetime.now(),
            }
            picking.tracking_state_history = [(0, 0, tracking_vals)]

            # Log tracking update
            picking.message_post(
                body=self.env._(
                    "Tracking updated: %(status)s - %(description)s",
                    status=tracking_data["status"],
                    description=tracking_data.get("description", ""),
                )
            )

    def dpd_pt_cancel_shipment(self, pickings):
        """Cancel DPD Portugal shipment."""
        for picking in pickings:
            if not picking.carrier_tracking_ref:
                continue

            response = self._dpd_pt_request_with_account(
                f"shipment/cancel/{picking.carrier_tracking_ref}", {}, picking
            ).json()

            if response.get("success", False):
                picking.message_post(
                    body=self.env._(
                        "DPD Portugal shipment %(tracking_ref)s cancelled",
                        tracking_ref=picking.carrier_tracking_ref,
                    )
                )
                picking.carrier_tracking_ref = False
            else:
                raise UserError(
                    self.env._(
                        "Failed to cancel shipment: %(message)s",
                        message=response.get("message", "Unknown error"),
                    )
                )

    def _prepare_dpd_pt_shipment_data(self, source):
        """Prepare shipment data for DPD Portugal API."""
        # Get sender and recipient information
        if source.partner_id and source.warehouse_id:
            # Stock picking
            sender = source.warehouse_id.partner_id or source.company_id.partner_id
            recipient = source.partner_id
            weight = source.shipping_weight
        elif source.partner_shipping_id:
            # Sales order
            sender = source.company_id.partner_id
            recipient = source.partner_shipping_id
            weight = source.total_weight
        else:
            raise ValidationError(
                self.env._("Invalid source for shipment data preparation")
            )

        # Get package dimensions
        # In Odoo 19, packages are accessed via move_line_ids.result_package_id
        packages = source.move_line_ids.result_package_id
        if packages:
            # Use first package dimensions
            package = packages[0]
            dimensions = {
                "length": package.length or 10,
                "width": package.width or 10,
                "height": package.height or 10,
            }
        elif self.dpd_portugal_default_package_type_id:
            # Use default package type dimensions
            package_type = self.dpd_portugal_default_package_type_id
            dimensions = {
                "length": package_type.length or 10,
                "width": package_type.width or 10,
                "height": package_type.height or 10,
            }
        else:
            # Default dimensions
            dimensions = {"length": 10, "width": 10, "height": 10}

        # Prepare shipment data
        shipment_data = {
            "sender": {
                "name": sender.name,
                "street": sender.street,
                "city": sender.city,
                "zip": sender.zip,
                "country": sender.country_id.code,
                "phone": sender.phone,
                "email": sender.email,
            },
            "recipient": {
                "name": recipient.name,
                "street": recipient.street,
                "city": recipient.city,
                "zip": recipient.zip,
                "country": recipient.country_id.code,
                "phone": recipient.phone
                if not self.dpd_portugal_hide_recipient_phone
                else None,
                "email": recipient.email
                if not self.dpd_portugal_hide_recipient_email
                else None,
            },
            "package": {
                "weight": weight,
                "length": dimensions["length"],
                "width": dimensions["width"],
                "height": dimensions["height"],
                "reference": getattr(source, "name", "")
                or getattr(source, "origin", ""),
            },
            "service": {
                "level": self.dpd_portugal_service_type,
                "saturday_delivery": self.dpd_portugal_saturday_delivery,
                "predict": self.dpd_portugal_predict_enabled,
                "cod": {
                    "enabled": self.dpd_portugal_cod_enabled,
                    "amount": getattr(source, "dpd_portugal_cod_amount", 0.0),
                },
                "insurance": {
                    "enabled": self.dpd_portugal_insurance_enabled,
                    "amount": self.dpd_portugal_insurance_amount,
                },
            },
        }

        return shipment_data

    def _validate_dpd_pt_picking(self, picking):
        """Validate picking data for DPD Portugal shipment."""
        required_fields = ["partner_id", "warehouse_id"]
        missing_fields = [
            field for field in required_fields if not getattr(picking, field, None)
        ]

        if missing_fields:
            raise ValidationError(
                self.env._(
                    "Missing required fields: %(fields)s",
                    fields=", ".join(missing_fields),
                )
            )

        # Validate addresses
        self._validate_dpd_pt_address(
            picking.warehouse_id.partner_id or picking.company_id.partner_id, "sender"
        )
        self._validate_dpd_pt_address(picking.partner_id, "recipient")

    def _validate_dpd_pt_address(self, partner, address_type):
        """Validate address for DPD Portugal shipment."""
        required_fields = ["name", "street", "city", "zip", "country_id"]
        missing_fields = [
            field for field in required_fields if not getattr(partner, field, None)
        ]

        if missing_fields:
            raise ValidationError(
                self.env._(
                    "Missing required fields for %(address_type)s address: %(fields)s",
                    address_type=address_type,
                    fields=", ".join(missing_fields),
                )
            )

    def _dpd_pt_get_api_url(self):
        """Get API URL based on environment."""
        return PROD_BASE_URL if self.prod_environment else TEST_BASE_URL

    def _dpd_pt_request_with_account(self, method, data, picking):
        """Execute a DPD Portugal API request using delivery_carrier_account.

        :param method: API method name (e.g. 'shipment/create', 'shipment/rate')
        :param data: dict of key/value pairs for the API data parameter
        :param picking: stock.picking record (used to resolve the account)
        :return: response object
        """
        account = picking._get_carrier_account()
        if not account or not account.account or not account.password:
            raise UserError(
                self.env._("Please configure a DPD Portugal carrier account.")
            )

        base_url = self._dpd_pt_get_api_url()
        full_url = f"{base_url}/{method.lstrip('/')}"

        headers = {"Content-Type": "application/json"}

        # Use HTTP Basic Auth with account credentials
        auth = (account.account, account.password)

        _logger.info("DPD Portugal %s request", method)

        try:
            response = requests.post(
                url=full_url,
                json=data,
                headers=headers,
                auth=auth,
                timeout=30,
            )
        except requests.exceptions.RequestException as exc:
            raise UserError(
                self.env._("DPD Portugal connection error: %(error)s", error=exc)
            ) from exc

        if response.status_code not in (200, 201):
            error_msg = self._dpd_pt_extract_error_message(response)
            raise UserError(
                self.env._(
                    "DPD Portugal API error (HTTP %(code)s): %(text)s",
                    code=response.status_code,
                    text=error_msg,
                )
            )

        _logger.info("DPD Portugal %s response OK", method)
        return response

    def _dpd_pt_extract_error_message(self, response):
        """Extract error message from API response."""
        try:
            error_data = response.json()
            if isinstance(error_data, dict):
                return (
                    error_data.get("message")
                    or error_data.get("error")
                    or response.text
                )
        except ValueError:
            _logger.debug("Failed to parse JSON error response: %s", response.text)
        return response.text
