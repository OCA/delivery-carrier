# Copyright 2020 Hunki Enterprises BV
# Copyright 2021 Tecnativa - Víctor Martínez
# Copyright 2024 Sygel - Manuel Regidor
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import datetime
import logging
from urllib.parse import urlencode

import requests

from odoo import _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)
UPS_TAX_IDENTIFICATION_NUMBER_MAX_LENGTH = 15


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
        status = self._send_request(
            url, data=data, headers=headers, auth=(self.client_id, self.client_secret)
        )
        status = status.json()
        self._raise_for_status(status, False)
        token = status.get("access_token")
        self.token = token
        self.carrier.ups_token = token
        self.carrier.ups_token_expiration_date = (
            datetime.datetime.now()
            + datetime.timedelta(seconds=int(status.get("expires_in")))
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
        status = self._send_request(url, json, data, headers, method, timeout=timeout)
        # Generate a new token
        if status.status_code == 401:
            self._get_new_token()
            headers["Authorization"] = f"Bearer {self.token}"
            status = self._send_request(
                url, json, data, headers, method, timeout=timeout
            )
        status = status.json()
        ups_last_request = f"URL: {self.url}\nData: {data}\nJSON: {json}"
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
        """Return a dict describing a partner for the shipping request"""
        address_dict = dict(
            AddressLine=self._build_address_lines(partner),
            City=partner.city,
            StateProvinceCode=partner.state_id.code,
            PostalCode=partner.zip,
            CountryCode=self._get_country_code(partner),
        )

        # Add ResidentialAddressIndicator if it's a residential address
        if partner._is_ups_residential_address():
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

    def _prepare_create_shipping(self, picking):
        """Return a dict that can be passed to the shipping endpoint of the UPS API"""
        packages_ids = (
            picking.move_ids.move_line_ids
            and picking.move_ids.move_line_ids.mapped("result_package_id")
        )
        if self.use_packages_from_picking and packages_ids:
            # modelo: stock.quant.package
            packages = [
                self._quant_package_data_from_picking(package, picking, True)
                for package in packages_ids
            ]
        else:
            # modelo: stock.package.type
            packages = []
            package_info = self._quant_package_data_from_picking(
                self.default_packaging_id, picking, False
            )
            package_weight = round(
                (picking.shipping_weight / (picking.number_of_packages or 1)), 2
            )
            for i in range(0, picking.number_of_packages):
                package_item = package_info.copy()
                package_name = f"{picking.name} ({i+1})"
                package_item["Description"] = package_name
                package_item["NumOfPieces"] = "1"
                package_item["Packaging"]["Description"] = package_name
                package_item["PackageWeight"]["Weight"] = str(package_weight)
                packages.append(package_item)

        partner_from = (
            picking.picking_type_id.warehouse_id.partner_id
            or picking.company_id.partner_id
        )
        partner_to = picking.partner_id
        ship_from = self._partner_to_shipping_data(partner_from)
        ship_to = self._partner_to_shipping_data(partner_to)
        same_origin_and_dest = self._is_same_origin_dest(partner_from, partner_to)
        if same_origin_and_dest and not ship_to["Phone"]["Number"]:
            ship_to.pop("Phone")

        vals = {
            "ShipmentRequest": {
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
            vals["ShipmentRequest"]["Shipment"]["ShipmentServiceOptions"] = (
                {
                    "COD": {
                        "CODFundsCode": picking.carrier_id.ups_cod_funds_code,
                        "CODAmount": {
                            "CurrencyCode": picking.sale_id.currency_id.name,
                            "MonetaryValue": str(picking.sale_id.amount_total),
                        },
                    }
                },
            )
        self._add_global_checkout_to_shipment(vals, picking)
        return vals

    def _add_global_checkout_to_shipment(self, vals, picking):
        """Attach the UPS Global Checkout Quote ID and DDP billing to a shipment.

        When the picking carries a Global Checkout Quote ID, the Quote ID is sent
        in the dedicated ``Shipment.QuoteID`` field (linking the guaranteed
        duties/taxes) and a second shipment charge of type ``02`` (Duties and
        Taxes) is billed to the shipper so UPS clears customs as Delivered Duty
        Paid (DDP).
        """
        quote_id = picking.ups_landed_cost_quote_identifier
        if not quote_id:
            return vals
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
        return vals

    def _send_shipping(self, picking):
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
        if self.negotiated_rates:
            vals["RateRequest"]["Shipment"]["ShipmentRatingOptions"] = {
                "NegotiatedRatesIndicator": "Y"
            }
        return vals

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
            msg = _("UPS Global Checkout error: {}").format(
                "\n".join(error.get("message", "") for error in errors)
            )
            if skip_errors:
                _logger.info(msg)
            else:
                raise UserError(msg)

    def _send_graphql(self, query, variables=None, skip_errors=False, timeout=15):
        """Send a GraphQL request to the UPS Global Checkout endpoint.

        Reuses the standard OAuth token handling from ``_process_reply`` and adds
        the required ``shipperNumber`` header.
        """
        payload = {"query": query}
        if variables is not None:
            payload["variables"] = variables
        status_json = self._process_reply(
            url=self._gc_url(),
            json=payload,
            headers_extra={
                "shipperNumber": self.shipper_number,
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            timeout=timeout,
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

    def _gc_item_inputs(self, order):
        """Build the item inputs (one per sale order line with a product)."""
        currency = order.currency_id.name
        items = []
        for line in order.order_line.filtered(
            lambda x: x.product_id and not x.display_type
        ):
            quantity = int(line.product_uom_qty) or 1
            item = {
                "amount": line.price_unit,
                "quantity": quantity,
                "currencyCode": currency,
                "description": (line.product_id.name or line.name or "")[:255],
            }
            origin_country = (
                line.product_id.country_of_origin
                if "country_of_origin" in line.product_id._fields
                else False
            )
            if origin_country:
                item["countryOfOrigin"] = origin_country.code
            hs_code = self._gc_product_hs_code(line.product_id)
            if hs_code:
                item["hsCode"] = hs_code
            if line.product_id.default_code:
                item["productId"] = line.product_id.default_code
            items.append(item)
        return items

    def landed_cost_quote(self, order, transportation_cost):
        """Run the UPS Global Checkout landed cost workflow for an order.

        The quote is a multi-step workflow bound to a Root resource created via
        ``rootCreate``; the subsequent workflow mutations attach to that root
        within the same session. Returns a dict with ``quote_id``, ``amount``,
        ``currency`` and ``guarantee_code``.
        """
        currency = order.currency_id.name
        variables = {
            "parties": self._gc_party_inputs(order),
            "items": self._gc_item_inputs(order),
            "rating": {
                "amount": transportation_cost,
                "currencyCode": currency,
                "serviceLevelCode": self.service_code,
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
    $rating: ShipmentRatingCreateWorkflowInput!
    $landedCost: LandedCostWorkFlowInput!
) {
    rootCreate { id }
    partyCreateWorkflow(input: $parties) { id }
    itemCreateWorkflow(input: $items) { id }
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
                _("UPS Global Checkout returned no landed cost for this order.")
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
            picking.write({"tracking_json": shipment, "pod_error": False})
        except Exception as ex:
            picking.write({"pod_error": str(ex)})
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
