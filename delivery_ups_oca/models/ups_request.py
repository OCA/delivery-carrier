# Copyright 2020 Hunki Enterprises BV
# Copyright 2021 Tecnativa - Víctor Martínez
# Copyright 2024 Sygel - Manuel Regidor
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import ast
import datetime
import logging
from urllib.parse import urlencode

import requests

from odoo import _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class UpsRequest:
    def __init__(self, carrier):
        self.carrier = carrier
        self.default_packaging_id = self.carrier.ups_default_packaging_id
        self.use_packages_from_picking = self.carrier.ups_use_packages_from_picking
        self.shipper_number = self.carrier.ups_shipper_number
        self.service_code = self.carrier.ups_service_code
        self.file_format = self.carrier.ups_file_format
        self.package_dimension_code = self.carrier.ups_package_dimension_code
        self.package_weight_code = self.carrier.ups_package_weight_code
        self.transaction_src = f"Odoo ({self.carrier.name})"
        self.client_id = self.carrier.ups_client_id
        self.client_secret = self.carrier.ups_client_secret
        self.token = self.carrier.ups_token
        self.token_expiration_date = self.carrier.ups_token_expiration_date
        self.negotiated_rates = self.carrier.ups_negotiated_rates
        self.url = "https://wwwcie.ups.com"
        if self.carrier.prod_environment:
            self.url = "https://onlinetools.ups.com"

    def _raise_for_status(self, status, skip_errors=True):
        errors = status.get("response", {}).get("errors")
        if errors:
            msg = _("Sending to UPS: {}").format(
                "\n".join("{code} {message}".format(**error) for error in errors),
            )
            if skip_errors:
                _logger.info(msg)
            else:
                raise UserError(msg)

    def _send_request(
        self,
        url,
        json=None,
        data=None,
        headers=None,
        method="post",
        auth=None,
        timeout=None,
    ):
        return getattr(requests, method)(
            url, data=data, json=json, headers=headers, auth=auth, timeout=timeout
        )

    def _get_new_token(self):
        if not (self.client_id and self.client_secret):
            raise UserError(
                _(
                    "Both Client ID and Client Secret"
                    " must be set in UPS delivery carriers."
                )
            )
        url = f"{self.url}/security/v1/oauth/token"
        headers = {"x-merchant-id": self.client_id}
        data = {"grant_type": "client_credentials"}
        # Log token request

        _logger.debug(
            "UPS Token Request: URL=%s, Headers=%s, Data=%s", url, headers, data
        )

        status = self._send_request(
            url, data=data, headers=headers, auth=(self.client_id, self.client_secret)
        )
        status_json = status.json()

        # Log token response
        # Mask the token in logs for security
        debug_response = (
            status_json.copy() if isinstance(status_json, dict) else status_json
        )
        if isinstance(debug_response, dict) and "access_token" in debug_response:
            debug_response["access_token"] = "***MASKED***"
        _logger.debug(
            "UPS Token Response: Status=%s, Content=%s",
            status.status_code,
            debug_response,
        )

        self._raise_for_status(status_json, False)
        token = status_json.get("access_token")
        self.token = token
        self.carrier.ups_token = token
        self.carrier.ups_token_expiration_date = (
            datetime.datetime.now()
            + datetime.timedelta(seconds=int(status_json.get("expires_in")))
        )

    def _process_reply(
        self,
        url,
        json=None,
        data=None,
        method="post",
        headers_extra=None,
        timeout=10,
    ):
        if (
            not self.token
            or not self.token_expiration_date
            or (self.token_expiration_date <= datetime.datetime.now())
        ):
            self._get_new_token()
        data = data or {}
        headers = {
            "Authorization": f"Bearer {self.token}",
        }
        if headers_extra:
            headers = {**headers, **headers_extra}

        # Log request details
        # Only include relevant parameters in the log
        # Token requests use data parameter, all other requests use json parameter
        body_data = json and json or data
        _logger.debug(
            "UPS Request: URL=%s, Method=%s, Headers=%s, Body=%s",
            url,
            method,
            headers,
            body_data,
        )

        status = self._send_request(url, json, data, headers, method, timeout=timeout)
        # Generate a new token
        if status.status_code == 401:
            self._get_new_token()
            # Update headers with the new token
            headers["Authorization"] = "Bearer {}"

            # Log the retry request
            # Only include relevant parameters in the log
            _logger.debug(
                "UPS Retry Request with new token: URL=%s, Method=%s, "
                "Headers=%s, Body=%s",
                url,
                method,
                headers,
                body_data,
            )

            status = self._send_request(
                url, json, data, headers, method, timeout=timeout
            )
        status_json = status.json()
        ups_last_request = f"URL: {self.url}\nData: {data}\nJSON: {json}"
        self.carrier.log_xml(ups_last_request, "ups_last_request")
        self.carrier.log_xml(status_json or "", "ups_last_response")
        return status_json

    def _quant_package_data_from_picking(self, package, picking, is_package=False):
        NumOfPieces = picking.number_of_packages
        PackageWeight = picking.shipping_weight
        if is_package:
            NumOfPieces = sum(package.mapped("quant_ids.quantity"))
            PackageWeight = max(package.shipping_weight, package.weight)
            package = package.package_type_id
        return {
            "Description": package.name,
            "NumOfPieces": str(NumOfPieces),
            "Packaging": {
                "Code": package.shipper_package_code,
                "Description": package.name,
            },
            "Dimensions": {
                "UnitOfMeasurement": {"Code": self.package_dimension_code},
                "Length": str(package.packaging_length),
                "Width": str(package.width),
                "Height": str(package.height),
            },
            "PackageWeight": {
                "UnitOfMeasurement": {"Code": self.package_weight_code},
                "Weight": str(PackageWeight),
            },
        }

    def _build_address_lines(self, partner):
        """Build UPS-compatible address lines with max 35 chars and up to 3 lines."""
        full_address = f"{partner.street or ''} {partner.street2 or ''}".strip()
        if not full_address:
            return [""]
        lines = []
        remaining = full_address
        for _i in range(3):
            if not remaining:
                break
            if len(remaining) <= 35:
                lines.append(remaining.strip())
                break
            split_at = remaining.rfind(" ", 0, 36)
            if split_at <= 0:
                split_at = 35
            lines.append(remaining[:split_at].strip())
            remaining = remaining[split_at:]
        return lines

    def _partner_to_shipping_data(self, partner, **kwargs):
        """Return a dict describing a partner for the shipping request"""
        address_dict = dict(
            AddressLine=self._build_address_lines(partner),
            City=partner.city,
            StateProvinceCode=partner.state_id.code,
            PostalCode=partner.zip,
            CountryCode=partner.country_id.code,
        )

        # Add ResidentialAddressIndicator if it's a residential address
        if partner._is_residential_address():
            address_dict["ResidentialAddressIndicator"] = ""

        result = dict(
            **kwargs,
            Name=((partner.parent_id or partner).name or "")[:35],
            AttentionName=(partner.name or "")[:35],
            TaxIdentificationNumber=partner.vat,
            EMailAddress=partner.email,
            Address=address_dict,
        )

        # Only add phone if it exists
        phone_number = partner.phone or partner.mobile
        if phone_number:
            result["Phone"] = dict(Number=phone_number)
        return result

    def _label_data(self):
        # When PDF is selected,
        # request GIF from UPS API since UPS doesn't support PDF natively
        api_format = "GIF" if self.file_format == "PDF" else self.file_format
        res = {"LabelImageFormat": {"Code": api_format}}
        # According to documentation, we need to specify sizes in some formats
        if api_format != "GIF":
            res["LabelStockSize"] = {"Height": "6", "Width": "4"}
        return res

    def _add_insurance_to_package(
        self, package_item, picking, package_weight=None, total_weight=None
    ):
        """Add insurance to a package if configured"""
        if not (hasattr(picking, "declared_value") and picking.declared_value > 0):
            return package_item

        # Add insurance if amount is positive
        if picking.declared_value > 0:
            if "PackageServiceOptions" not in package_item:
                package_item["PackageServiceOptions"] = {}
            package_item["PackageServiceOptions"]["DeclaredValue"] = {
                "CurrencyCode": picking.company_id.currency_id.name,
                "MonetaryValue": str(round(picking.declared_value, 2)),
            }

        return package_item

    def _prepare_packages_from_picking(self, picking):
        """Prepare packages data from picking packages"""
        packages = []

        if self.use_packages_from_picking and picking.move_line_ids.mapped(
            "result_package_id"
        ):
            # Use actual packages from the picking
            for package in picking.move_line_ids.mapped("result_package_id"):
                package_item = self._quant_package_data_from_picking(
                    package, picking, True
                )

                # Add insurance if configured
                package_weight = float(package_item["PackageWeight"]["Weight"])
                package_item = self._add_insurance_to_package(
                    package_item, picking, package_weight, picking.shipping_weight
                )

                packages.append(package_item)
        else:
            # Create packages based on default packaging
            package_info = self._quant_package_data_from_picking(
                self.default_packaging_id, picking, False
            )

            # Calculate package weight
            if picking.number_of_packages > 0:
                package_weight = round(
                    (picking.shipping_weight / picking.number_of_packages), 2
                )
            else:
                package_weight = picking.shipping_weight

            # Ensure at least one package is created
            num_packages = max(1, picking.number_of_packages)

            for i in range(0, num_packages):
                package_item = package_info.copy()
                package_name = f"{picking.name} ({i+1})"
                package_item["Description"] = package_name
                package_item["NumOfPieces"] = "1"
                package_item["Packaging"]["Description"] = package_name
                package_item["PackageWeight"]["Weight"] = str(package_weight)

                # Add insurance if configured
                package_item = self._add_insurance_to_package(package_item, picking)

                packages.append(package_item)

        return packages

    def _prepare_shipment_service_options(self, picking):
        """Prepare shipment service options including COD and paperless invoice"""
        shipment_service_options = {}

        # Add COD if enabled
        if picking.carrier_id.ups_cash_on_delivery and picking.sale_id:
            shipment_service_options["COD"] = {
                "CODFundsCode": picking.carrier_id.ups_cod_funds_code,
                "CODAmount": {
                    "CurrencyCode": picking.sale_id.currency_id.name,
                    "MonetaryValue": str(picking.sale_id.amount_total),
                },
            }

        # Add paperless invoice if document_id exists and is not empty
        if picking.document_id and picking.document_id.strip():
            try:
                # Try to convert the document_id to a list if it's a string
                # representation of a list
                document_id = (
                    ast.literal_eval(picking.document_id)
                    if len(picking.document_id) > 30
                    else picking.document_id
                )
                shipment_service_options["InternationalForms"] = {
                    "FormType": "07",
                    "UserCreatedForm": {"DocumentID": document_id},
                }
            except (ValueError, SyntaxError):
                # If it's not a valid Python literal, use it as is
                shipment_service_options["InternationalForms"] = {
                    "FormType": "07",
                    "UserCreatedForm": {"DocumentID": picking.document_id},
                }

        return shipment_service_options

    def _prepare_create_shipping(self, picking):
        """Return a dict that can be passed to the shipping endpoint of the UPS API"""
        # Prepare packages
        packages = self._prepare_packages_from_picking(picking)

        # Build the base request structure
        vals = {
            "ShipmentRequest": {
                "Shipment": {
                    "Description": picking.name,
                    "Shipper": self._partner_to_shipping_data(
                        partner=picking.company_id.partner_id,
                        ShipperNumber=self.shipper_number,
                    ),
                    "ShipTo": self._partner_to_shipping_data(picking.partner_id),
                    "ShipFrom": self._partner_to_shipping_data(
                        picking.picking_type_id.warehouse_id.partner_id
                        or picking.company_id.partner_id
                    ),
                    "PaymentInformation": {
                        "ShipmentCharge": {
                            "Type": "01",
                            "BillShipper": {
                                # we ignore the alternatives paying per credit card or
                                # paypal for now
                                "AccountNumber": self.shipper_number,
                            },
                        }
                    },
                    "Service": {"Code": self.service_code},
                    "Package": packages,
                },
                "LabelSpecification": self._label_data(),
            }
        }

        # Add negotiated rates if enabled
        if self.negotiated_rates:
            vals["ShipmentRequest"]["Shipment"]["ShipmentRatingOptions"] = {
                "NegotiatedRatesIndicator": "ABR"
            }

        # Add shipment service options (COD, paperless invoice)
        shipment_service_options = self._prepare_shipment_service_options(picking)
        if shipment_service_options:
            vals["ShipmentRequest"]["Shipment"]["ShipmentServiceOptions"] = (
                shipment_service_options
            )

            # Add ShipmentServiceOptions to the request if not empty
            if shipment_service_options:
                vals["ShipmentRequest"]["Shipment"]["ShipmentServiceOptions"] = (
                    shipment_service_options
                )

        return vals

    def _send_shipping(self, picking):
        # Check if we need to send paperless invoice
        if picking.ups_paperless_auto_send and not picking.document_id:
            try:
                self.carrier.ups_paperless_invoice_provider(picking)
            except Exception as e:
                error_msg = _("Failed to send paperless invoice: %s") % str(e)
                _logger.error(error_msg)
                raise UserError(error_msg) from e

        status = self._process_reply(
            url=f"{self.url}/api/shipments/v1/ship",
            json=self._prepare_create_shipping(picking),
        )
        self._raise_for_status(status, False)
        res = status["ShipmentResponse"]["ShipmentResults"]
        PackageResults = res["PackageResults"]
        labels = []
        if isinstance(PackageResults, dict):
            labels.append(
                {
                    "tracking_ref": PackageResults["TrackingNumber"],
                    "format_code": PackageResults["ShippingLabel"]["ImageFormat"][
                        "Code"
                    ],
                    "datas": PackageResults["ShippingLabel"]["GraphicImage"],
                }
            )
        if isinstance(PackageResults, list):
            for label in PackageResults:
                labels.append(
                    {
                        "tracking_ref": label["TrackingNumber"],
                        "format_code": label["ShippingLabel"]["ImageFormat"]["Code"],
                        "datas": label["ShippingLabel"]["GraphicImage"],
                    }
                )
        # Use negotiated rates if available and enabled
        if self.negotiated_rates and "NegotiatedRates" in res:
            price = res["NegotiatedRates"]["TotalCharge"]
        else:
            price = res["ShipmentCharges"]["TotalCharges"]

        return {
            "price": price,
            "ShipmentIdentificationNumber": res["ShipmentIdentificationNumber"],
            "labels": labels,
        }

    def _quant_package_data_from_order(self, order):
        PackageWeight = 0
        for line in order.order_line.filtered(
            lambda x: x.product_id and x.product_id.weight > 0
        ):
            PackageWeight += line.product_id.weight * line.product_uom_qty
        return {
            "PackagingType": {"Code": self.default_packaging_id.shipper_package_code},
            "Dimensions": {
                "UnitOfMeasurement": {"Code": self.package_dimension_code},
                "Length": str(self.default_packaging_id.packaging_length),
                "Width": str(self.default_packaging_id.width),
                "Height": str(self.default_packaging_id.height),
            },
            "PackageWeight": {
                "UnitOfMeasurement": {"Code": self.package_weight_code},
                "Weight": str(PackageWeight),
            },
        }

    def _prepare_rate_shipment(self, order):
        packages = [self._quant_package_data_from_order(order)]
        rate_request = {
            "RateRequest": {
                "Shipment": {
                    "Shipper": self._partner_to_shipping_data(
                        partner=order.company_id.partner_id,
                        ShipperNumber=self.shipper_number,
                    ),
                    "ShipTo": self._partner_to_shipping_data(order.partner_shipping_id),
                    "ShipFrom": self._partner_to_shipping_data(
                        order.warehouse_id.partner_id or order.company_id.partner_id
                    ),
                    "Service": {"Code": self.service_code},
                    "Package": packages,
                }
            }
        }

        # Add negotiated rates if enabled
        if self.negotiated_rates:
            rate_request["RateRequest"]["Shipment"]["ShipmentRatingOptions"] = {
                "NegotiatedRatesIndicator": "ABR"
            }

        return rate_request

    def _rate_shipment(self, order, skip_errors=False):
        status = self._process_reply(
            url=f"{self.url}/api/rating/v1/Rate",
            json=self._prepare_rate_shipment(order),
        )
        self._raise_for_status(status, skip_errors)
        return status

    def rate_shipment(self, order):
        status = self._rate_shipment(order)
        rated_shipment = status["RateResponse"]["RatedShipment"]

        # Use negotiated rates if available and enabled
        if self.negotiated_rates and "NegotiatedRateCharges" in rated_shipment:
            return rated_shipment["NegotiatedRateCharges"]["TotalCharge"]

        return rated_shipment["TotalCharges"]

    def _prepare_shipping_label(self, carrier_tracking_ref):
        return {
            "LabelRecoveryRequest": {
                "LabelSpecification": self._label_data(),
                "TrackingNumber": carrier_tracking_ref,
            }
        }

    def shipping_label(self, carrier_tracking_ref):
        status = self._process_reply(
            url=f"{self.url}/api/labels/v1/recovery",
            json=self._prepare_shipping_label(carrier_tracking_ref),
        )
        self._raise_for_status(status, False)
        labels = []
        labels_data = status["LabelRecoveryResponse"]["LabelResults"]
        if isinstance(labels_data, dict):
            labels.append(
                {
                    "tracking_ref": labels_data["TrackingNumber"],
                    "format_code": labels_data["LabelImage"]["LabelImageFormat"][
                        "Code"
                    ],
                    "datas": labels_data["LabelImage"]["GraphicImage"],
                }
            )
        elif isinstance(labels_data, list):
            for label in labels_data:
                labels.append(
                    {
                        "tracking_ref": label["TrackingNumber"],
                        "format_code": label["LabelImage"]["LabelImageFormat"]["Code"],
                        "datas": label["LabelImage"]["GraphicImage"],
                    }
                )

        return labels

    def cancel_shipment(self, picking):
        url = f"{self.url}/api/shipments/v1/void/cancel"
        url = f"{url}/{picking.carrier_tracking_ref}"
        status = self._process_reply(url=url, method="delete")
        self._raise_for_status(status, False)
        return True

    def tracking_state_update(self, picking):
        static_states = {
            "I": "in_transit",
            "D": "customer_delivered",
            "E": "incident",
            "P": "customer_delivered",
            "M": "in_transit",
        }
        params = {"returnSignature": "true", "returnPOD": "true"}
        query_string = urlencode(params)
        status = self._process_reply(
            url=f"{self.url}/api/track/v1/details/{picking.carrier_tracking_ref}?{query_string}",
            method="get",
            headers_extra={
                "transId": f"{datetime.datetime.now().timestamp()}",
                "transactionSrc": f"{picking.company_id.name} - Odoo",
            },
        )
        self._raise_for_status(status, False)
        shipment = status["trackResponse"]["shipment"][0]
        package = shipment["package"][0]
        current_status = package.get("currentStatus") or {}
        states_list = []
        delivery_state = "incident"
        tracking_state = f"[{current_status['code']}] {current_status['description']}"
        pod = (
            package.get("deliveryInformation", {}).get("pod", {}).get("content", False)
        )
        try:
            if not shipment.get("warnings"):
                for activity in shipment["package"][0]["activity"]:
                    states_list.append(
                        "{} - {}".format(
                            datetime.datetime.strptime(
                                "{}{}".format(
                                    activity.get("date"), activity.get("time")
                                ),
                                "%Y%m%d%H%M%S",
                            ),
                            activity.get("status").get("description"),
                        )
                    )
                if shipment["package"][0]["activity"]:
                    delivery_state = static_states.get(
                        shipment["package"][0]["activity"][0]["status"]["type"],
                        "incident",
                    )
            else:
                for warning in shipment.get("warnings"):
                    states_list.append(
                        _("{date} - Warning: {warn}").format(
                            date=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            warn=warning.get("message"),
                        )
                    )

        except Exception:
            states_list.append(
                _("{} - Error retrieving the tracking information.").format(
                    datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                )
            )
        return {
            "delivery_state": delivery_state,
            "tracking_state_history": "\n".join(states_list),
            "tracking_state": tracking_state,
            "pod": pod,
        }

    def send_paperless_invoice(self, picking, paperless_document_data):
        """Send paperless invoice documents to UPS"""
        if not paperless_document_data:
            raise UserError(_("No documents to send!"))

        request_data = {
            "UploadRequest": {
                "Request": {"TransactionReference": {"CustomerContext": ""}},
                "ShipperNumber": self.shipper_number,
                "UserCreatedForm": paperless_document_data,
            }
        }

        headers_extra = {
            "ShipperNumber": self.shipper_number,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        url = f"{self.url}/api/paperlessdocuments/v1/upload"

        # Use _process_reply for consistent auth handling and retry logic
        status_json = self._process_reply(
            url=url,
            json=request_data,
            headers_extra=headers_extra,
            timeout=10,
        )

        # Use standard error handling
        self._raise_for_status(status_json, skip_errors=False)

        # Extract document ID from response
        document_id = (
            status_json.get("UploadResponse", {})
            .get("FormsHistoryDocumentID", {})
            .get("DocumentID")
        )

        if not document_id:
            raise UserError(_("No document ID returned by UPS"))

        picking.document_id = document_id
        return document_id
