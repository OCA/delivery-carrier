# Copyright 2020 Hunki Enterprises BV
# Copyright 2021 Tecnativa - Víctor Martínez
# Copyright 2024 Sygel - Manuel Regidor
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import datetime
import json
import logging
import uuid
from urllib.parse import urlencode

import requests

from odoo.exceptions import UserError
from odoo.tools import float_compare

_logger = logging.getLogger(__name__)
UPS_TAX_IDENTIFICATION_NUMBER_MAX_LENGTH = 15
UPS_SHIP_API_VERSION = "v2409"
UPS_LABEL_API_VERSION = "v2603"
UPS_PAPERLESS_API_VERSION = "v2"
GC_DIM_UNIT = {"IN": "INCH", "CM": "CENTIMETER"}
GC_WEIGHT_UNIT = {"LBS": "POUND", "KGS": "KILOGRAM", "OZS": "OUNCE"}
GC_SERVICE_LEVEL = {
    "07": "ups.worldwide_express",
    "08": "ups.worldwide_expedited",
    "11": "ups.standard",
    "17": "ups.worldwide_economy_ddp",
    "54": "ups.worldwide_express_plus",
    "65": "ups.worldwide_saver",
    "71": "ups.worldwide_express_freight_midday",
    "72": "ups.worldwide_economy_ddp",
    "96": "ups.worldwide_express_freight",
}


class UpsRequest:
    def __init__(self, carrier):
        self.carrier = carrier
        self.env = carrier.env
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
        self.address_validation = self.carrier.ups_address_validation
        self.url = "https://wwwcie.ups.com"
        if self.carrier.prod_environment:
            self.url = "https://onlinetools.ups.com"

    def _raise_for_status(self, status, skip_errors=True):
        errors = status.get("response", {}).get("errors")
        if errors:
            msg = self.carrier.env._("Sending to UPS: {}").format(
                "\n".join("{code} {message}".format(**error) for error in errors),
            )
            if skip_errors:
                _logger.info(msg)
            else:
                raise UserError(msg)

    def _transaction_headers(self):
        return {
            "transId": uuid.uuid4().hex,
            "transactionSrc": self.transaction_src,
        }

    def _as_list(self, value):
        if not value:
            return []
        return value if isinstance(value, list) else [value]

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
                self.carrier.env._(
                    "Both Client ID and Client Secret"
                    " must be set in UPS delivery carriers."
                )
            )
        url = f"{self.url}/security/v1/oauth/token"
        headers = {"x-merchant-id": self.client_id}
        data = {"grant_type": "client_credentials"}
        _logger.debug(
            "UPS Token Request: URL=%s, Headers=%s, Data=%s", url, headers, data
        )
        status = self._send_request(
            url, data=data, headers=headers, auth=(self.client_id, self.client_secret)
        )
        status_code = status.status_code
        status = status.json()
        debug_response = status.copy() if isinstance(status, dict) else status
        if isinstance(debug_response, dict) and "access_token" in debug_response:
            debug_response["access_token"] = "***MASKED***"
        _logger.debug(
            "UPS Token Response: Status=%s, Content=%s",
            status_code,
            debug_response,
        )
        self._raise_for_status(status, False)
        token = status.get("access_token")
        self.token = token
        self.carrier.ups_token = token
        self.carrier.ups_token_expiration_date = (
            datetime.datetime.now()
            + datetime.timedelta(seconds=int(status.get("expires_in")))
        )

    def _send_authenticated_request(
        self,
        url,
        json=None,
        data=None,
        method="post",
        headers_extra=None,
        timeout=10,
    ):
        """Send a request with a valid bearer token, retrying once on a 401"""
        if (
            not self.token
            or not self.token_expiration_date
            or (self.token_expiration_date <= datetime.datetime.now())
        ):
            self._get_new_token()
        headers = {
            "Authorization": f"Bearer {self.token}",
        }
        if headers_extra:
            headers = {**headers, **headers_extra}
        debug_headers = {**headers, "Authorization": "***MASKED***"}
        _logger.debug(
            "UPS Request: URL=%s, Method=%s, Headers=%s, Body=%s",
            url,
            method,
            debug_headers,
            json or data,
        )
        response = self._send_request(url, json, data, headers, method, timeout=timeout)
        # Generate a new token
        if response.status_code == 401:
            self._get_new_token()
            headers["Authorization"] = f"Bearer {self.token}"
            _logger.debug("UPS request returned 401; retrying with a refreshed token")
            response = self._send_request(
                url, json, data, headers, method, timeout=timeout
            )
        return response

    def _process_reply(
        self,
        url,
        json=None,
        data=None,
        method="post",
        headers_extra=None,
        timeout=10,
    ):
        data = data or {}
        status = self._send_authenticated_request(
            url, json, data, method, headers_extra, timeout
        )
        status_code = status.status_code
        status = status.json()
        _logger.debug("UPS Response: Status=%s, Content=%s", status_code, status)
        ups_last_request = f"URL: {url}\nData: {data}\nJSON: {json}"
        self.carrier.log_xml(ups_last_request, "ups_last_request")
        self.carrier.log_xml(status or "", "ups_last_response")
        return status

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

    def _get_tax_identification_number(self, partner):
        # Remove any whitespace before enforcing UPS' 15-character limit.
        vat = "".join((partner.vat or "").split())
        return (
            vat
            if vat and len(vat) <= UPS_TAX_IDENTIFICATION_NUMBER_MAX_LENGTH
            else False
        )

    def _partner_to_shipping_data(self, partner, **kwargs):
        """Return a dict describing a partner for the shipping request

        UPS only accepts ResidentialAddressIndicator on the ShipTo address,
        flagged with the ``is_ship_to`` keyword argument.
        """
        is_ship_to = kwargs.pop("is_ship_to", False)
        address_dict = dict(
            AddressLine=self._build_address_lines(partner),
            City=partner.city,
            StateProvinceCode=partner.state_id.code,
            PostalCode=partner.zip,
            CountryCode=self._get_country_code(partner),
        )

        if is_ship_to and partner._is_ups_residential_address():
            address_dict["ResidentialAddressIndicator"] = ""

        vals = dict(
            **kwargs,
            Name=((partner.parent_id or partner).name or "")[:35],
            AttentionName=(partner.name or "")[:35],
            Phone=dict(Number=partner.phone or partner.mobile),
            EMailAddress=partner.email,
            Address=address_dict,
        )
        tax_identification_number = self._get_tax_identification_number(partner)
        if tax_identification_number:
            vals["TaxIdentificationNumber"] = tax_identification_number
        return vals

    def _get_country_code(self, partner):
        country_code = partner.country_id.code
        # The UPS API expects the country code to be XC for Ceuta and XL for Melilla
        special_state_codes = {"CE": "XC", "ME": "XL"}
        if (
            partner.country_id.code == "ES"
            and partner.state_id.code in special_state_codes
        ):
            country_code = special_state_codes[partner.state_id.code]
        return country_code

    def _label_data(self):
        # When PDF is selected,
        # request GIF from UPS API since UPS doesn't support PDF natively
        api_format = "GIF" if self.file_format == "PDF" else self.file_format
        res = {"LabelImageFormat": {"Code": api_format}}
        # According to documentation, we need to specify sizes in some formats
        if api_format != "GIF":
            res["LabelStockSize"] = {"Height": "6", "Width": "4"}
        return res

    def _is_same_origin_dest(self, ship_from, ship_to):
        if not ship_from.country_id or not ship_to.country_id:
            return False
        return ship_from.country_id.id == ship_to.country_id.id

    @staticmethod
    def _add_declared_value_to_package(package_item, picking):
        if picking.declared_value <= 0:
            return package_item
        package_item.setdefault("PackageServiceOptions", {})["DeclaredValue"] = {
            "CurrencyCode": picking.declared_value_currency_id.name,
            "MonetaryValue": str(round(picking.declared_value, 2)),
        }
        return package_item

    def _prepare_create_shipping(self, picking):
        """Return a dict that can be passed to the shipping endpoint of the UPS API"""
        if self.use_packages_from_picking and picking.move_line_ids.mapped(
            "result_package_id"
        ):
            # model: stock.quant.package
            packages = []
            for package in picking.move_line_ids.mapped("result_package_id"):
                package_item = self._quant_package_data_from_picking(
                    package, picking, True
                )
                package_item = self._add_declared_value_to_package(
                    package_item, picking
                )
                packages.append(package_item)
        else:
            # model: stock.package.type
            packages = []
            package_info = self._quant_package_data_from_picking(
                self.default_packaging_id, picking, False
            )
            number_of_packages = picking.number_of_packages or 1
            package_weight = round((picking.shipping_weight / number_of_packages), 2)
            for i in range(0, number_of_packages):
                package_item = package_info.copy()
                package_name = f"{picking.name} ({i+1})"
                package_item["Description"] = package_name
                package_item["NumOfPieces"] = "1"
                package_item["Packaging"]["Description"] = package_name
                package_item["PackageWeight"]["Weight"] = str(package_weight)
                package_item = self._add_declared_value_to_package(
                    package_item, picking
                )
                packages.append(package_item)

        partner_from = (
            picking.picking_type_id.warehouse_id.partner_id
            or picking.company_id.partner_id
        )
        partner_to = picking.partner_id
        ship_from = self._partner_to_shipping_data(partner_from)
        ship_to = self._partner_to_shipping_data(partner_to, is_ship_to=True)
        same_origin_and_dest = self._is_same_origin_dest(partner_from, partner_to)
        if same_origin_and_dest and not ship_to["Phone"]["Number"]:
            ship_to.pop("Phone")

        vals = {
            "ShipmentRequest": {
                "Request": {
                    "RequestOption": self.address_validation,
                    "TransactionReference": {"CustomerContext": picking.name},
                },
                "Shipment": {
                    "Description": picking.name,
                    "Shipper": self._partner_to_shipping_data(
                        partner=picking.company_id.partner_id,
                        ShipperNumber=self.shipper_number,
                    ),
                    "ShipTo": ship_to,
                    "ShipFrom": ship_from,
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
        if self.negotiated_rates:
            vals["ShipmentRequest"]["Shipment"]["ShipmentRatingOptions"] = {
                "NegotiatedRatesIndicator": "Y"
            }
        if picking.carrier_id.ups_cash_on_delivery and picking.sale_id:
            vals["ShipmentRequest"]["Shipment"]["ShipmentServiceOptions"] = {
                "COD": {
                    "CODFundsCode": picking.carrier_id.ups_cod_funds_code,
                    "CODAmount": {
                        "CurrencyCode": picking.sale_id.currency_id.name,
                        "MonetaryValue": str(picking.sale_id.amount_total),
                    },
                }
            }
        # Add paperless documents if a document id has been retrieved
        document_ids = picking._get_ups_document_ids()
        if document_ids:
            shipment = vals["ShipmentRequest"]["Shipment"]
            shipment.setdefault("ShipmentServiceOptions", {})["InternationalForms"] = {
                "FormType": ["07"],
                "UserCreatedForm": {"DocumentID": document_ids},
                "Product": self._get_ups_paperless_products(picking),
            }
        self._add_global_checkout_to_shipment(vals, picking)
        return vals

    def _get_ups_paperless_products(self, picking):
        """Product descriptions for the InternationalForms container. UPS requires
        the Product element, but with only Description mandatory, as the invoice
        data itself comes from the uploaded user created forms (FormType 07)."""
        products = []
        for move in picking.move_ids.filtered(
            lambda m: m.product_id and m.product_id.type != "service"
        ):
            product = move.product_id.with_context(lang="en_US")
            products.append({"Description": [(product.name or move.name or "")[:35]]})
        return products or [{"Description": [(picking.name or "")[:35]]}]

    def _add_global_checkout_to_shipment(self, vals, picking):
        """Attach the UPS Global Checkout Quote ID and DDP billing to a shipment.

        When the picking carries a Global Checkout Quote ID, the Quote ID is sent
        in the dedicated ``Shipment.QuoteID`` field (linking the guaranteed
        duties/taxes) and a second shipment charge of type ``02`` (Duties and
        Taxes) is billed to the shipper so UPS clears customs as Delivered Duty
        Paid (DDP).
        """
        order = picking.sale_id
        quote_id = picking.ups_landed_cost_quote_identifier or (
            order.ups_landed_cost_quote_identifier if order else False
        )
        # If the order no longer has a landed cost line, the customer is not being
        # charged duties, so do not apply Global Checkout DDP to the shipment.
        if order and quote_id and not order.order_line.filtered("is_ups_landed_cost"):
            picking.message_post(
                body=self.carrier.env._(
                    "UPS Global Checkout DDP was not applied: the duties, taxes & "
                    "fees line was removed from the order, so the shipment is sent "
                    "without a Quote ID."
                )
            )
            picking.ups_landed_cost_quote_identifier = False
            quote_id = False
        if not quote_id:
            return vals
        # Persist onto the picking when it was quoted after the picking existed.
        if picking.ups_landed_cost_quote_identifier != quote_id:
            picking.ups_landed_cost_quote_identifier = quote_id
        shipment = vals["ShipmentRequest"]["Shipment"]
        shipment["QuoteID"] = quote_id
        # Bill duties and taxes to the shipper (DDP) in addition to transportation.
        shipment_charge = shipment["PaymentInformation"]["ShipmentCharge"]
        if isinstance(shipment_charge, dict):
            shipment_charge = [shipment_charge]
        shipment_charge.append(
            {
                "Type": "02",
                "BillShipper": {"AccountNumber": self.shipper_number},
            }
        )
        shipment["PaymentInformation"]["ShipmentCharge"] = shipment_charge
        self._add_global_checkout_international_forms(shipment, picking)
        return vals

    def _add_global_checkout_international_forms(self, shipment, picking):
        """Add the UPS-generated customs invoice (InternationalForms) with the
        commodity data that must match the Global Checkout quote (quantity,
        value, origin country, currency and part number).

        Also guard the destination country/state to match the quote, since UPS
        requires ShipTo Country/State to be identical to the quote parties.
        """
        order = picking.sale_id
        if not order:
            return
        self._check_global_checkout_destination(order, picking)
        service_options = shipment.setdefault("ShipmentServiceOptions", {})
        existing = service_options.get("InternationalForms", {})
        # An uploaded commercial invoice replaces the UPS-generated one, also for
        # Global Checkout, to avoid two commercial invoices at customs.
        use_uploaded_invoice = bool(
            existing
            and "002" in picking.ups_paperless_document_ids.mapped("ups_document_type")
        )
        commodities = self._gc_commodities(order)
        if not commodities:
            return
        currency = order.currency_id.name
        products = []
        for commodity in commodities:
            product = {
                "Description": [commodity["description"][:35]],
                "Unit": {
                    "Number": str(commodity["quantity"]),
                    "Value": str(commodity["amount"]),
                    "UnitOfMeasurement": {"Code": "EA"},
                },
            }
            if commodity["product_id"]:
                product["PartNumber"] = commodity["product_id"]
            if commodity["origin_country"]:
                product["OriginCountryCode"] = commodity["origin_country"]
            if commodity["hs_code"]:
                product["CommodityCode"] = commodity["hs_code"]
            products.append(product)
        if use_uploaded_invoice:
            # Keep FormType 07 only, but still pass the commodity data, which
            # UPS needs to calculate duties and taxes for DDP.
            service_options["InternationalForms"] = {
                **existing,
                "ReasonForExport": (
                    picking.ups_global_checkout_reason_for_export or "SALE"
                ),
                "CurrencyCode": currency,
                "Product": products,
            }
            return
        sold_to = self._partner_to_shipping_data(picking.partner_id)
        sold_to.get("Address", {}).pop("ResidentialAddressIndicator", None)
        # Merge into any InternationalForms already set (e.g. the paperless
        # UserCreatedForm, FormType 07) instead of overwriting it.
        form_types = ["01"] + [
            form_type for form_type in existing.get("FormType", []) if form_type != "01"
        ]
        service_options["InternationalForms"] = {
            **existing,
            "FormType": form_types,
            "InvoiceDate": datetime.date.today().strftime("%Y%m%d"),
            "InvoiceNumber": (order.name or picking.name)[:35],
            "ReasonForExport": (
                picking.ups_global_checkout_reason_for_export or "SALE"
            ),
            "CurrencyCode": currency,
            "Contacts": {"SoldTo": sold_to},
            "Product": products,
        }

    def _check_global_checkout_destination(self, order, picking):
        """Ensure the shipment destination matches the quote destination, as UPS
        requires ShipTo Country/State to be identical to the Global Checkout
        quote."""
        quote_partner = order.partner_shipping_id
        ship_partner = picking.partner_id
        if self._get_country_code(quote_partner) != self._get_country_code(
            ship_partner
        ) or (quote_partner.state_id.code != ship_partner.state_id.code):
            raise UserError(
                self.carrier.env._(
                    "The delivery address does not match the address used for the "
                    "UPS Global Checkout quote. Re-calculate the shipping rate "
                    "before shipping."
                )
            )

    def _send_shipping(self, picking):
        # Send the paperless documents first so their document IDs are included
        # in the shipment request.
        if picking.ups_paperless_auto_send and not picking.ups_document_identifier:
            try:
                self.carrier.send_ups_paperless_documents(picking)
            except Exception as e:
                error_msg = self.carrier.env._(
                    "Failed to send paperless documents: %s"
                ) % str(e)
                _logger.error(error_msg)
                raise UserError(error_msg) from e
        status = self._process_reply(
            url=f"{self.url}/api/shipments/{UPS_SHIP_API_VERSION}/ship",
            json=self._prepare_create_shipping(picking),
            headers_extra=self._transaction_headers(),
        )
        self._raise_for_status(status, False)
        res = status["ShipmentResponse"]["ShipmentResults"]
        labels = [
            {
                "tracking_ref": package["TrackingNumber"],
                "format_code": package["ShippingLabel"]["ImageFormat"]["Code"],
                "datas": package["ShippingLabel"]["GraphicImage"],
            }
            for package in self._as_list(res.get("PackageResults"))
        ]
        if self.negotiated_rates and "NegotiatedRateCharges" in res:
            price = res["NegotiatedRateCharges"]["TotalCharge"]
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
        vals = {
            "RateRequest": {
                "Request": {
                    "TransactionReference": {"CustomerContext": order.name},
                },
                "Shipment": {
                    "Shipper": self._partner_to_shipping_data(
                        partner=order.company_id.partner_id,
                        ShipperNumber=self.shipper_number,
                    ),
                    "ShipTo": self._partner_to_shipping_data(
                        order.partner_shipping_id, is_ship_to=True
                    ),
                    "ShipFrom": self._partner_to_shipping_data(
                        order.warehouse_id.partner_id or order.company_id.partner_id
                    ),
                    "Service": {"Code": self.service_code},
                    "Package": packages,
                },
            }
        }
        if self.negotiated_rates:
            vals["RateRequest"]["Shipment"]["ShipmentRatingOptions"] = {
                "NegotiatedRatesIndicator": "Y"
            }
        return vals

    def _rate_shipment(self, order, skip_errors=False):
        status = self._process_reply(
            url=f"{self.url}/api/rating/{UPS_SHIP_API_VERSION}/Rate",
            json=self._prepare_rate_shipment(order),
            headers_extra=self._transaction_headers(),
        )
        self._raise_for_status(status, skip_errors)
        return status

    def rate_shipment(self, order):
        status = self._rate_shipment(order)
        rated_shipments = self._as_list(status["RateResponse"].get("RatedShipment"))
        if not rated_shipments:
            raise UserError(
                self.carrier.env._("UPS returned no rate for this shipment.")
            )
        rated_shipment = rated_shipments[0]
        if self.negotiated_rates and "NegotiatedRateCharges" in rated_shipment:
            return rated_shipment["NegotiatedRateCharges"]["TotalCharge"]
        return rated_shipment["TotalCharges"]

    # -------------------------------------------------------------------------
    # UPS Global Checkout (landed cost) - GraphQL API
    # -------------------------------------------------------------------------
    def _gc_url(self):
        return f"{self.url}/api/globalcheckout/v1/graphql"

    def _raise_for_graphql_errors(self, status_json, skip_errors=True):
        errors = (status_json or {}).get("errors")
        if errors:
            msg = self.carrier.env._("UPS Global Checkout error: {}").format(
                "\n".join(error.get("message", "") for error in errors)
            )
            if skip_errors:
                _logger.info(msg)
            else:
                raise UserError(msg)

    def _send_graphql(self, query, variables=None, skip_errors=False):
        """Send a GraphQL request to the UPS Global Checkout endpoint.

        Reuses the standard OAuth token handling from ``_process_reply`` and adds
        the required ``shipperNumber`` header.
        """
        payload = {"query": query}
        if variables is not None:
            payload["variables"] = variables
        _logger.debug(
            "UPS Global Checkout GraphQL Request: URL=%s, ShipperNumber=%s, Body=%s",
            self._gc_url(),
            self.shipper_number,
            payload,
        )
        status_json = self._process_reply(
            url=self._gc_url(),
            json=payload,
            headers_extra={
                "shipperNumber": self.shipper_number,
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
        )
        self._raise_for_graphql_errors(status_json, skip_errors)
        return (status_json or {}).get("data") or {}

    def _gc_party_inputs(self, order):
        """Build the ORIGIN and DESTINATION party inputs for the workflow."""
        partner_from = order.warehouse_id.partner_id or order.company_id.partner_id
        partner_to = order.partner_shipping_id

        def _location(partner):
            location = {"countryCode": self._get_country_code(partner)}
            if partner.zip:
                location["postalCode"] = partner.zip
            if partner.state_id.code:
                location["administrativeAreaCode"] = partner.state_id.code
            if partner.city:
                location["locality"] = partner.city
            return location

        return [
            {"type": "ORIGIN", "location": _location(partner_from)},
            {"type": "DESTINATION", "location": _location(partner_to)},
        ]

    def _gc_product_hs_code(self, product):
        """Return the HS code to send to UPS Global Checkout for a product.

        When the OCA ``product_harmonized_system`` module is installed, the full
        national code (``hs.code.local_code``, including extension digits beyond
        the 6-digit HS heading) is used, resolved recursively so a code set on
        the product category is also taken into account. If no such code can be
        resolved, it falls back to the core ``hs_code`` field provided by the
        ``stock_delivery`` module.
        """
        if hasattr(product, "get_hs_code_recursively"):
            hs_record = product.get_hs_code_recursively()
            if hs_record:
                return hs_record.local_code or hs_record.hs_code
        return getattr(product, "hs_code", False)

    def _gc_product_origin_country(self, product):
        country = False
        if "origin_country_id" in product._fields:
            country = product.origin_country_id
        if not country and "country_of_origin" in product._fields:
            country = product.country_of_origin
        return country.code if country else False

    def _gc_commodities(self, order):
        """Normalized commodity data shared by the Global Checkout quote and the
        customs invoice on the shipment, so the values UPS requires to match
        (quantity, value, origin country, currency, part number) are identical by
        construction."""
        currency = order.currency_id.name
        commodities = []
        for line in order.order_line.filtered(
            lambda x: x.product_id
            and not x.display_type
            and not x.is_delivery
            and not x.is_ups_landed_cost
            and x.product_id.type != "service"
            and float_compare(
                x.product_uom_qty, 0.0, precision_rounding=x.product_uom.rounding
            )
            > 0
        ):
            product = line.product_id
            product_en = product.with_context(lang="en_US")
            commodities.append(
                {
                    "description": (product_en.name or line.name or "")[:255],
                    "quantity": int(line.product_uom_qty) or 1,
                    "amount": order.currency_id.round(line.price_unit),
                    "currency": currency,
                    "origin_country": self._gc_product_origin_country(product),
                    "hs_code": self._gc_product_hs_code(product),
                    "product_id": product.default_code or product.barcode or False,
                }
            )
        return commodities

    def _gc_item_inputs(self, order):
        """Build the item inputs (one per sale order line with a product and a
        positive quantity)."""
        items = []
        for commodity in self._gc_commodities(order):
            item = {
                "amount": commodity["amount"],
                "quantity": commodity["quantity"],
                "currencyCode": commodity["currency"],
                "description": commodity["description"],
            }
            if commodity["origin_country"]:
                item["countryOfOrigin"] = commodity["origin_country"]
            if commodity["hs_code"]:
                item["hsCode"] = commodity["hs_code"]
            if commodity["product_id"]:
                item["productId"] = commodity["product_id"]
            items.append(item)
        return items

    def _gc_carton_inputs(self, order):
        carton = {
            "dimensionalUnit": GC_DIM_UNIT.get(
                self.package_dimension_code, "CENTIMETER"
            ),
            "weightUnit": GC_WEIGHT_UNIT.get(self.package_weight_code, "KILOGRAM"),
            "weight": order._get_estimated_weight() or 0.1,
            "type": "PACKAGE",
        }
        pkg = self.default_packaging_id
        if pkg and pkg.packaging_length and pkg.width and pkg.height:
            carton["length"] = pkg.packaging_length
            carton["width"] = pkg.width
            carton["height"] = pkg.height
        return [carton]

    def landed_cost_quote(self, order, transportation_cost):
        """Run the UPS Global Checkout landed cost workflow for an order.

        The quote is a multi-step workflow bound to a Root resource created via
        ``rootCreate``; the subsequent workflow mutations attach to that root
        within the same session. Returns a dict with ``quote_id``, ``amount``,
        ``currency`` and ``guarantee_code``.
        """
        currency = order.currency_id.name
        service_level_code = GC_SERVICE_LEVEL.get(self.service_code)
        if not service_level_code:
            raise UserError(
                self.carrier.env._(
                    "UPS Global Checkout does not support the configured UPS "
                    "service (%s). Select an international UPS service on the "
                    "delivery method."
                )
                % self.service_code
            )
        variables = {
            "parties": self._gc_party_inputs(order),
            "items": self._gc_item_inputs(order),
            "cartons": self._gc_carton_inputs(order),
            "rating": {
                "amount": transportation_cost,
                "currencyCode": currency,
                "serviceLevelCode": service_level_code,
            },
            "landedCost": {
                "currencyCode": currency,
                "calculationMethod": "DDP_PREFERRED",
            },
        }
        query = """
mutation OdooLandedCost(
    $parties: [PartyCreateWorkflowInput!]!
    $items: [ItemCreateWorkflowInput!]!
    $cartons: [CartonCreateWorkflowInput!]!
    $rating: ShipmentRatingCreateWorkflowInput!
    $landedCost: LandedCostWorkFlowInput!
) {
    rootCreate { id }
    partyCreateWorkflow(input: $parties) { id }
    itemCreateWorkflow(input: $items) { id }
    cartonsCreateWorkflow(input: $cartons) { id }
    shipmentRatingCreateWorkflow(input: $rating) { id }
    landedCostCalculateWorkflow(input: $landedCost) {
        id
        currencyCode
        landedCostGuaranteeCode
        amountSubtotals { landedCostTotal duties taxes fees }
    }
}
"""
        data = self._send_graphql(query, variables, skip_errors=False)
        results = data.get("landedCostCalculateWorkflow") or []
        if not results:
            raise UserError(
                self.carrier.env._(
                    "UPS Global Checkout returned no landed cost for this order."
                )
            )
        landed_cost = results[0]
        subtotals = landed_cost.get("amountSubtotals") or {}
        return {
            "quote_id": landed_cost["id"],
            "amount": subtotals.get("landedCostTotal") or 0.0,
            "currency": landed_cost.get("currencyCode") or currency,
            "guarantee_code": landed_cost.get("landedCostGuaranteeCode"),
        }

    def _prepare_shipping_label(self, carrier_tracking_ref):
        return {
            "LabelRecoveryRequest": {
                "Request": {
                    "TransactionReference": {"CustomerContext": carrier_tracking_ref},
                },
                "LabelSpecification": self._label_data(),
                "TrackingNumber": carrier_tracking_ref,
            }
        }

    def shipping_label(self, carrier_tracking_ref):
        status = self._process_reply(
            url=f"{self.url}/api/labels/{UPS_LABEL_API_VERSION}/recovery",
            json=self._prepare_shipping_label(carrier_tracking_ref),
            headers_extra=self._transaction_headers(),
        )
        self._raise_for_status(status, False)
        labels_data = status["LabelRecoveryResponse"].get("LabelResults")
        return [
            {
                "tracking_ref": label["TrackingNumber"],
                "format_code": label["LabelImage"]["LabelImageFormat"]["Code"],
                "datas": label["LabelImage"]["GraphicImage"],
            }
            for label in self._as_list(labels_data)
        ]

    def cancel_shipment(self, picking):
        url = f"{self.url}/api/shipments/{UPS_SHIP_API_VERSION}/void/cancel"
        url = f"{url}/{picking.carrier_tracking_ref}"
        status = self._process_reply(
            url=url, method="delete", headers_extra=self._transaction_headers()
        )
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
        url = (
            f"{self.url}/api/track/v1/details"
            f"/{picking.carrier_tracking_ref}?{query_string}"
        )
        status = self._process_reply(
            url=url,
            method="get",
            headers_extra=self._transaction_headers(),
        )
        self._raise_for_status(status, False)
        shipment = status["trackResponse"]["shipment"][0]
        # UPS omits the package (only returns warnings) when the tracking
        # information is not found yet
        package = (shipment.get("package") or [{}])[0]
        current_status = package.get("currentStatus") or {}
        states_list = []
        delivery_state = picking.delivery_state or "incident"
        tracking_state = picking.tracking_state or False
        if current_status:
            tracking_state = (
                f"[{current_status.get('code')}] {current_status.get('description')}"
            )
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
                        self.carrier.env._("{date} - Warning: {warn}").format(
                            date=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            warn=warning.get("message"),
                        )
                    )
            picking.write({"tracking_json": shipment, "pod_error": False})
        except Exception as ex:
            picking.write({"pod_error": str(ex)})
            states_list.append(
                self.carrier.env._(
                    "{} - Error retrieving the tracking information."
                ).format(
                    datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                )
            )
        return {
            "delivery_state": delivery_state,
            "tracking_state_history": "\n".join(states_list),
            "tracking_state": tracking_state,
            "pod": pod,
        }

    def _normalize_document_ids(self, document_id):
        if not document_id:
            return []
        if isinstance(document_id, str):
            document_id = [document_id]
        return [doc_id.strip() for doc_id in document_id if doc_id and doc_id.strip()]

    def _log_paperless_alerts(self, upload_response):
        """Log the alerts of an upload response and return them as a text block"""
        alerts = (upload_response.get("Response") or {}).get("Alert") or []
        if isinstance(alerts, dict):
            alerts = [alerts]
        messages = []
        for alert in alerts:
            _logger.info(
                "UPS Paperless Documents alert: %s %s",
                alert.get("Code"),
                alert.get("Description"),
            )
            messages.append(f"{alert.get('Code')} {alert.get('Description')}")
        return "\n".join(messages)

    def send_paperless_documents(self, picking, paperless_document_data):
        """Send paperless documents to UPS"""
        if not paperless_document_data:
            raise UserError(picking.env._("No documents to send!"))

        request_data = {
            "UploadRequest": {
                "Request": {"TransactionReference": {"CustomerContext": picking.name}},
                "ShipperNumber": self.shipper_number,
                "UserCreatedForm": paperless_document_data,
            }
        }
        headers = {
            "ShipperNumber": self.shipper_number,
            "Content-Type": "application/json",
            "Accept": "application/json",
            "transId": uuid.uuid4().hex,
            "transactionSrc": self.transaction_src,
        }
        url = f"{self.url}/api/paperlessdocuments/{UPS_PAPERLESS_API_VERSION}/upload"
        # Mask the document files before logging the request
        debug_request = json.loads(json.dumps(request_data))
        for doc in debug_request.get("UploadRequest", {}).get("UserCreatedForm", []):
            if "UserCreatedFormFile" in doc:
                doc["UserCreatedFormFile"] = "***MASKED***"
        _logger.debug(
            "UPS Paperless Documents Request: URL=%s, Headers=%s, Data=%s",
            url,
            headers,
            debug_request,
        )
        self.carrier.log_xml(f"URL: {url}\nJSON: {debug_request}", "ups_last_request")
        try:
            response = self._send_authenticated_request(
                url,
                data=json.dumps(request_data),
                headers_extra=headers,
                timeout=10,
            )
            _logger.debug(
                "UPS Paperless Documents Response: Status=%s, Content=%s",
                response.status_code,
                response.text,
            )
            self.carrier.log_xml(response.text or "", "ups_last_response")
            # UPS answers server errors with an HTML page instead of JSON, so the
            # payload is parsed defensively before looking at the status code.
            try:
                payload = json.loads(response.text)
            except (ValueError, TypeError):
                payload = None
            if response.status_code in [200, 201] and payload is not None:
                upload_response = payload.get("UploadResponse") or {}
                alerts = self._log_paperless_alerts(upload_response)
                forms_history = upload_response.get("FormsHistoryDocumentID") or {}
                document_ids = self._normalize_document_ids(
                    forms_history.get("DocumentID")
                )
                if not document_ids:
                    _logger.error(
                        "UPS Paperless Documents upload returned HTTP %s without any "
                        "DocumentID: %s",
                        response.status_code,
                        response.text,
                    )
                    raise UserError(
                        picking.env._(
                            "UPS accepted the Paperless Documents upload but did "
                            "not return any Document ID.%s"
                        )
                        % (f"\n{alerts}" if alerts else "")
                    ) from None
                picking.ups_document_identifier = ",".join(document_ids)
                return document_ids
            _logger.error(
                "UPS Paperless Documents upload failed: Status=%s, Content=%s",
                response.status_code,
                response.text,
            )
            if payload is None:
                raise UserError(
                    picking.env._(
                        "UPS Paperless Documents upload failed (HTTP %s). "
                        "UPS returned a non-JSON response, which usually means "
                        "a temporary UPS or network (edge/CDN) outage. "
                        "Please retry in a few minutes; if the problem "
                        "persists, contact UPS support."
                    )
                    % response.status_code
                ) from None
            errors = (payload.get("response") or {}).get("errors")
            error_message = errors[0].get("message") if errors else response.text
            raise UserError(
                picking.env._("Paperless Documents: %s") % error_message
            ) from None
        except UserError:
            raise
        except Exception as e:
            # Connection errors and timeouts otherwise surface as an empty or
            # cryptic message, so log the traceback and keep the exception type.
            _logger.exception("UPS Paperless Documents upload failed")
            raise UserError(
                picking.env._("UPS Paperless Documents upload failed: %s")
                % (str(e) or type(e).__name__)
            ) from e
