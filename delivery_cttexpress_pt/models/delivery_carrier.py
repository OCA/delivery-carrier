# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import base64

from odoo import api, fields, models
from odoo.exceptions import UserError

from .cttexpress_pt_master_data import (
    CTTEXPRESS_PT_EXPORT_TYPES,
    CTTEXPRESS_PT_SUB_PRODUCTS,
    CTTEXPRESS_PT_UPU_CODES,
)
from .cttexpress_pt_request import CTTExpressPTRequest


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    delivery_type = fields.Selection(
        selection_add=[("cttexpress_pt", "CTT Express Portugal")],
        ondelete={"cttexpress_pt": "set default"},
    )
    cttexpress_pt_authentication_id = fields.Char(string="Authentication ID")
    cttexpress_pt_client_id = fields.Char(string="Client ID")
    cttexpress_pt_contract_id = fields.Char(string="Contract ID")
    cttexpress_pt_distribution_channel_id = fields.Integer(
        string="Distribution Channel ID", default=99
    )
    cttexpress_pt_user_id = fields.Char(string="User ID")
    cttexpress_pt_test_authentication_id = fields.Char(string="Test Authentication ID")
    cttexpress_pt_test_client_id = fields.Char(string="Test Client ID")
    cttexpress_pt_test_contract_id = fields.Char(string="Test Contract ID")
    cttexpress_pt_test_distribution_channel_id = fields.Integer(
        string="Test Distribution Channel ID"
    )
    cttexpress_pt_test_user_id = fields.Char(string="Test User ID")
    cttexpress_pt_sub_product = fields.Selection(
        selection=CTTEXPRESS_PT_SUB_PRODUCTS,
        string="Sub product",
    )
    cttexpress_pt_label_type = fields.Selection(
        selection=[("pdf", "PDF"), ("zpl", "ZPL")],
        string="Label type",
        default="pdf",
    )
    cttexpress_pt_has_sender_information = fields.Boolean(
        string="Sender information on label"
    )
    cttexpress_pt_export_type = fields.Selection(
        selection=CTTEXPRESS_PT_EXPORT_TYPES,
        string="Export type",
        default="Permanent",
    )
    cttexpress_pt_upc_code = fields.Selection(
        selection=CTTEXPRESS_PT_UPU_CODES,
        string="UPU code",
        default="Goods",
    )

    @api.onchange("delivery_type")
    def _onchange_delivery_type_cttexpress_pt(self):
        """Default price method for CTT as the API can't gather prices."""
        if self.delivery_type == "cttexpress_pt":
            self.price_method = "base_on_rule"

    def _cttexpress_pt_credentials(self, prod):
        """Return the e-pool credential set for the given environment.

        Test fields fall back to the production values when left empty.
        """

        def field(name):
            if not prod:
                return getattr(self, f"cttexpress_pt_test_{name}") or getattr(
                    self, f"cttexpress_pt_{name}"
                )
            return getattr(self, f"cttexpress_pt_{name}")

        return {
            "authentication_id": field("authentication_id"),
            "client_id": field("client_id"),
            "contract_id": field("contract_id"),
            "distribution_channel_id": field("distribution_channel_id"),
            "user_id": field("user_id"),
        }

    def _cttexpress_pt_request(self, prod):
        """Get CTT Express Portugal Request object.

        :param bool prod: Use the production endpoint and credentials
        :return CTTExpressPTRequest: API request object
        """
        creds = self._cttexpress_pt_credentials(prod)
        return CTTExpressPTRequest(
            authentication_id=creds["authentication_id"],
            client_id=creds["client_id"],
            contract_id=creds["contract_id"],
            distribution_channel_id=creds["distribution_channel_id"],
            user_id=creds["user_id"],
            prod=prod,
        )

    @api.model
    def _cttexpress_pt_log_request(self, ctt_request):
        """When debug is active requests/responses will be logged in ir.logging

        :param ctt_request ctt_request: CTT Express request object
        """
        if ctt_request.ctt_last_request:
            self.log_xml(ctt_request.ctt_last_request, "cttexpress_pt_request")
        if ctt_request.ctt_last_response:
            self.log_xml(ctt_request.ctt_last_response, "cttexpress_pt_response")

    @staticmethod
    def _cttexpress_pt_as_list(value):
        """Normalize a serialized SOAP value to a list."""
        if not value:
            return []
        return value if isinstance(value, list) else [value]

    @api.model
    def _cttexpress_pt_check_errors(self, response):
        """Raise a readable error when the API returns an ErrorsList.

        :param dict response: Serialized API response
        :raises UserError: with the API error messages
        """
        errors = (response or {}).get("ErrorsList") or {}
        error_data = self._cttexpress_pt_as_list(errors.get("ErrorData"))
        messages = []
        for item in error_data:
            code = item.get("ErrorCode") or item.get("Code") or ""
            message = item.get("Message") or ""
            messages.append(f"{code} - {message}" if code else message)
        messages = [message for message in messages if message]
        if messages:
            raise UserError(
                self.env._(
                    "CTT Express Portugal rejected the request:\n%s",
                    "\n".join(messages),
                )
            )

    @api.model
    def _cttexpress_pt_shipment_outputs(self, response):
        """Return the ShipmentDataOutput list of a CreateShipment response."""
        shipment_data = (response or {}).get("ShipmentData") or {}
        return self._cttexpress_pt_as_list(shipment_data.get("ShipmentDataOutput"))

    @api.model
    def _cttexpress_pt_check_address(self, partner, required_fields=None):
        """Check that a partner has the address fields required by CTT.

        :param record partner: `res.partner` record
        :param list required_fields: field names to check
        :return str: error message or empty string
        """
        required_fields = required_fields or ["zip", "city", "country_id", "street"]
        missing = [field for field in required_fields if not partner[field]]
        if missing:
            return self.env._(
                "Missing values for address: %s",
                ", ".join(missing).replace("_id", ""),
            )
        return ""

    @staticmethod
    def _cttexpress_pt_phone(phone):
        # Phone formats can't have spaces and must include the country prefix
        if not phone:
            return ""
        res = phone.replace(" ", "").replace("(", "").replace(")", "").replace("-", "")
        if not res.startswith("+") and not res.startswith("00"):
            res = "+351" + res
        return res

    def _cttexpress_pt_phones(self, partner):
        """Return (phone, mobile) normalized for the CTT API.

        CTT rejects a mobile number in the Phone field, so mobile-looking
        numbers are routed to MobilePhone.
        """
        phone = self._cttexpress_pt_phone(partner.phone)
        mobile = self._cttexpress_pt_phone(
            getattr(partner, "mobile", False)
            or getattr(partner.commercial_partner_id, "mobile", False)
        )
        digits = "".join(c for c in phone if c.isdigit())
        if phone and (
            phone == mobile
            or digits.startswith("3519")
            or (len(digits) == 9 and digits.startswith("9"))
        ):
            mobile = mobile or phone
            phone = ""
        return phone, mobile

    def _cttexpress_pt_prepare_address(self, partner, address_type):
        """Build the AddressData dict for a partner.

        :param record partner: `res.partner` record
        :param str address_type: AddressTypeValues (Sender, Receiver, ...)
        :return dict: AddressData values for the API
        """
        phone, mobile = self._cttexpress_pt_phones(partner)
        address = {
            "Address": " ".join([partner.street or "", partner.street2 or ""]).strip(),
            "City": partner.city or "",
            "ContactName": partner.name or "",
            "Country": partner.country_id.code or "",
            "Door": "",
            "Email": partner.email or "",
            "Floor": "",
            "MobilePhone": mobile,
            "Name": partner.commercial_partner_id.name or partner.name or "",
            "Phone": phone,
            "Type": address_type,
        }
        if partner.country_id and partner.country_id.code == "PT":
            zip_parts = (partner.zip or "").split("-")
            # PTZipCode3/4 are int in the WSDL but keep the string form so
            # leading zeros are preserved; empty values must be None.
            address["PTZipCode4"] = zip_parts[0] or None
            address["PTZipCode3"] = (
                zip_parts[1] if len(zip_parts) > 1 and zip_parts[1] else None
            )
            address["PTZipCodeLocation"] = partner.city or ""
        else:
            address["NonPTZipCode"] = partner.zip or ""
            address["NonPTZipCodeLocation"] = partner.city or ""
        return address

    def _cttexpress_pt_prepare_shipping(self, picking):
        """Convert picking values for the CTT Express Portugal API.

        :param record picking: `stock.picking` record
        :return dict: DeliveryNote values for CreateShipment
        """
        self.ensure_one()
        shipper_partner = (
            picking.picking_type_id.warehouse_id.partner_id
            or picking.company_id.partner_id
        )
        recipient = picking.partner_id
        errors = []
        shipper_error = self._cttexpress_pt_check_address(shipper_partner)
        if shipper_error:
            errors.append(self.env._("Shipper address: %s", shipper_error))
        recipient_error = self._cttexpress_pt_check_address(recipient)
        if recipient_error:
            errors.append(self.env._("Recipient address: %s", recipient_error))
        if not picking.shipping_weight:
            errors.append(self.env._("Shipping weight is missing."))
        if errors:
            raise UserError("\n".join(errors))

        quantity = picking.number_of_packages or 1
        shipment_ctt = {
            "HasSenderInformation": self.cttexpress_pt_has_sender_information,
            "ReceiverData": self._cttexpress_pt_prepare_address(recipient, "Receiver"),
            "SenderData": self._cttexpress_pt_prepare_address(
                shipper_partner, "Sender"
            ),
            "ShipmentData": {
                "ClientReference": picking.name or "",
                "DeclaredValue": picking.sale_id.amount_total or 0.0,
                "ExportType": self.cttexpress_pt_export_type,
                "IsDevolution": False,
                "Observations": "",
                "Quantity": quantity,
                # Weight is sent in grams per package
                "Weight": int(1000 * picking.shipping_weight / quantity) or 1,
                "UPUCode": self.cttexpress_pt_upc_code,
            },
        }
        if self.cttexpress_pt_sub_product == "EMSF056.01":
            shipment_ctt["SpecialServices"] = {
                "SpecialService": [
                    {
                        "SpecialServiceType": "MultipleHomeDelivery",
                        "MultipleHomeDelivery": {
                            "AttemptsNumber": 1,
                            "InNonDeliveryCase": "PostOfficeNotiffied",
                        },
                    }
                ]
            }
        creds = self._cttexpress_pt_credentials(prod=self.prod_environment)
        return {
            "ClientId": creds["client_id"],
            "ContractId": creds["contract_id"],
            "DistributionChannelId": creds["distribution_channel_id"],
            "ShipmentCTT": {"ShipmentCTT": [shipment_ctt]},
            "SubProductId": self.cttexpress_pt_sub_product,
        }

    @api.model
    def _cttexpress_pt_document_attachments(self, documents, default_name):
        """Return (filename, content) tuples for API DocumentData entries."""
        return [
            (
                document.get("FileName") or default_name,
                base64.b64decode(document.get("File") or ""),
            )
            for document in self._cttexpress_pt_as_list(documents)
        ]

    def _cttexpress_pt_label_attachments(self, picking, shipment_output):
        """Return the shipping label attachments for a ShipmentDataOutput."""
        if self.cttexpress_pt_label_type == "zpl":
            return [
                (
                    label.get("FileName") or f"{picking.name}.zpl",
                    label.get("Label") or "",
                )
                for label in self._cttexpress_pt_as_list(
                    (shipment_output.get("LabelList") or {}).get("LabelData")
                )
            ]
        return self._cttexpress_pt_document_attachments(
            (shipment_output.get("DocumentsList") or {}).get("DocumentData"),
            f"{picking.name}.pdf",
        )

    def cttexpress_pt_send_shipping(self, pickings):
        """CTT Express Portugal wildcard method called on picking validation.

        Creates the shipment, attaches the label and closes it to obtain
        the carrier manifest (CA1) document.

        :param record pickings: `stock.picking` recordset
        :raises UserError: On any API error
        :return list: dicts with tracking number and delivery price (0)
        """
        self.ensure_one()
        ctt_request = self._cttexpress_pt_request(prod=self.prod_environment)
        result = []
        for picking in pickings:
            delivery_note = self._cttexpress_pt_prepare_shipping(picking)
            response = ctt_request.create_shipment(delivery_note)
            self._cttexpress_pt_log_request(ctt_request)
            self._cttexpress_pt_check_errors(response)
            shipment_outputs = self._cttexpress_pt_shipment_outputs(response)
            if not shipment_outputs:
                raise UserError(self.env._("CTT Express returned no shipment data."))
            shipment_output = shipment_outputs[0]
            first_object = shipment_output.get("FirstObject")
            last_object = shipment_output.get("LastObject")
            picking.message_post(
                body=self.env._("CTT Express shipment created"),
                attachments=self._cttexpress_pt_label_attachments(
                    picking, shipment_output
                ),
            )
            close_response = ctt_request.close_shipment(
                [
                    {
                        "FirstObjectCode": first_object,
                        "LastObjectCode": last_object,
                        "SubProductCode": self.cttexpress_pt_sub_product,
                    }
                ]
            )
            self._cttexpress_pt_log_request(ctt_request)
            self._cttexpress_pt_check_errors(close_response)
            picking.message_post(
                body=self.env._("CTT Express shipment closed"),
                attachments=self._cttexpress_pt_document_attachments(
                    (close_response.get("DocumentsList") or {}).get("DocumentData"),
                    "CA1.pdf",
                ),
            )
            result.append({"exact_price": 0.0, "tracking_number": first_object})
        return result

    def cttexpress_pt_rate_shipment(self, order):
        """The API can't gather prices; validate addresses instead.

        :param record order: `sale.order` record
        :return dict: rate_shipment result, price is always 0
        """
        self.ensure_one()
        shipper_error = self._cttexpress_pt_check_address(order.warehouse_id.partner_id)
        recipient_error = self._cttexpress_pt_check_address(order.partner_shipping_id)
        product_weight = order.order_line.filtered(
            lambda line: not line.is_delivery
            and line.product_id.is_storable
            and line.product_id.weight <= 0
        )
        if shipper_error or recipient_error or product_weight:
            error_message = ""
            if shipper_error:
                error_message += self.env._("Shipper address: %s\n", shipper_error)
            if recipient_error:
                error_message += self.env._("Recipient address: %s\n", recipient_error)
            if product_weight:
                product_name = ", ".join(
                    product_weight.mapped("product_id").mapped("name")
                )
                error_message += self.env._(
                    "Product weight is not available: %s", product_name
                )
            return {
                "success": False,
                "price": 0.0,
                "error_message": error_message,
                "warning_message": False,
            }
        return {
            "success": True,
            "price": 0.0,
            "error_message": False,
            "warning_message": False,
        }

    def cttexpress_pt_cancel_shipment(self, pickings):
        """The e-pool API has no shipment cancellation operation."""
        raise UserError(
            self.env._(
                "CTT Express Portugal API does not support cancelling shipments."
            )
        )

    def cttexpress_pt_get_tracking_link(self, picking):
        """CTT Express Portugal wildcard method for the tracking link."""
        return "https://www.ctt.pt/feapl_2/app/open/objectSearch/objectSearch.jspx?request_locale=en"

    def action_cttexpress_pt_test_connection(self):
        """Probe the configured CTT Express Portugal endpoints.

        The ShipmentProvider service has no ping operation, so a
        CloseShipment for nonexistent object codes is used: the ErrorsList
        reply proves connectivity and authentication without side effects.
        """
        self.ensure_one()
        results = []
        for label, prod in (
            (self.env._("Production"), True),
            (self.env._("Test"), False),
        ):
            if not prod and not self.cttexpress_pt_test_authentication_id:
                continue
            ctt_request = self._cttexpress_pt_request(prod=prod)
            try:
                response = ctt_request.test_connection()
            except Exception as e:
                raise UserError(
                    self.env._(
                        "Could not reach the %(label)s CTT Express endpoint: %(error)s",
                        label=label,
                        error=e,
                    )
                ) from e
            self._cttexpress_pt_log_request(ctt_request)
            error_data = self._cttexpress_pt_as_list(
                ((response or {}).get("ErrorsList") or {}).get("ErrorData")
            )
            auth_failed = any(
                item.get("ErrorCode") == "EW0001"
                or "autentica" in (item.get("Message") or "").lower()
                for item in error_data
            )
            if auth_failed:
                raise UserError(
                    self.env._("%s endpoint rejected the credentials.", label)
                )
            results.append(self.env._("%s endpoint: credentials accepted", label))
        if not results:
            raise UserError(self.env._("No CTT Express endpoint configured."))
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": self.env._("CTT Express Portugal"),
                "message": "\n".join(results),
                "type": "success",
                "sticky": True,
            },
        }
