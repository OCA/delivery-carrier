# Copyright 2020 Hunki Enterprises BV
# Copyright 2021 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import logging

import requests

from odoo import _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class UpsRequest(object):
    def __init__(self, carrier):
        self.carrier = carrier
        self.access_license_number = self.carrier.ups_access_license
        self.username = self.carrier.ups_ws_username
        self.password = self.carrier.ups_ws_password
        self.default_packaging_id = self.carrier.ups_default_packaging_id
        self.shipper_number = self.carrier.ups_shipper_number
        self.service_code = self.carrier.ups_service_code
        self.file_format = self.carrier.ups_file_format
        self.package_dimension_code = self.carrier.ups_package_dimension_code
        self.package_weight_code = self.carrier.ups_package_weight_code
        self.transaction_src = "Odoo (%s)" % self.carrier.name
        self.url = "https://wwwcie.ups.com"
        if self.carrier.prod_environment:
            self.url = "https://onlinetools.ups.com"

    def _process_reply(
        self, url, data=None, method="post", query_parameters=None,
    ):
        headers = {
            "AccessLicenseNumber": self.access_license_number,
            "Username": self.username,
            "Password": self.password,
            "transactionSrc": self.transaction_src,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        status = getattr(requests, method)(
            url, json=data, headers=headers, params=query_parameters
        ).json()
        ups_last_request = ("URL: {}\nData: {}").format(self.url, data)
        self.carrier.log_xml(ups_last_request, "ups_last_request")
        self.carrier.log_xml(status or "", "ups_last_response")
        errors = status.get("response", {}).get("errors")
        if errors:
            raise ValidationError(
                _("Error on Sending to UPS: \n\n%s")
                % ("\n".join("%(code)s %(message)s" % error for error in errors),)
            )
        return status

    def _format_dimweight(self, dimweight):
        if not dimweight:
            return "0"
        return str(round(dimweight / 5000, 1)).replace(".", "")

    def _quant_package_data_from_picking(self, package, picking, is_package=True):
        NumOfPieces = picking.number_of_packages
        PackageWeight = picking.shipping_weight
        if is_package:
            NumOfPieces = sum(package.mapped("quant_ids.quantity"))
            PackageWeight = package.weight
        DimWeight = 0
        if not (package.length * package.width * package.height):
            for line in picking.move_lines.filtered(lambda x: x.product_id.volume):
                DimWeight += line.product_id.volume * line.product_uom_qty
        else:
            DimWeight = package.length * package.width * package.height
        DeclaredValue = ""
        if picking.ups_insurance:
            CurrencyCode = (
                picking.sale_id.currency_id.name or picking.company_id.currency_id.name
            )
            MonetaryValue = str(picking.ups_insurance_value)
            DeclaredValue = {
                "DeclaredValue": {
                    "CurrencyCode": CurrencyCode,
                    "MonetaryValue": MonetaryValue,
                }
            }
        return {
            "Description": package.name,
            "NumOfPieces": str(NumOfPieces),
            "Packaging": {
                "Code": package.shipper_package_code,
                "Description": package.name,
            },
            "Dimensions": {
                "UnitOfMeasurement": {"Code": self.package_dimension_code},
                "Length": str(package.length),
                "Width": str(package.width),
                "Height": str(package.height),
            },
            "PackageWeight": {
                "UnitOfMeasurement": {"Code": self.package_weight_code},
                "Weight": str(PackageWeight)
                if PackageWeight
                else str(DimWeight / 5000),
            },
            "DimWeight": {
                "UnitOfMeasurement": {"Code": self.package_weight_code},
                "Weight": self._format_dimweight(DimWeight),
            },
            "PackageServiceOptions": DeclaredValue,
        }

    def _partner_to_shipping_data(self, partner, **kwargs):
        """Return a dict describing a partner for the shipping request"""
        country_code = partner.country_id.code
        state_code = partner.state_id.code
        if country_code == "ES" and state_code in ["TF", "GC"]:
            # Canary Islands (and others) have a special country code
            # https://en.wikipedia.org/wiki/ISO_3166-1
            country_code = "IC"
        if country_code not in ["US", "CA", "IC"]:
            state_code = ""
        return dict(
            **kwargs,
            Name=(partner.parent_id or partner).name,
            AttentionName=partner.name,
            TaxIdentificationNumber=partner.vat or "",
            Phone=dict(Number=partner.phone or partner.mobile),
            EMailAddress=partner.email or "",
            Address=dict(
                AddressLine=[partner.street, partner.street2 or ""],
                City=partner.city,
                StateProvinceCode=state_code,
                PostalCode=partner.zip,
                CountryCode=country_code,
            ),
        )

    def _label_data(self):
        res = {"LabelImageFormat": {"Code": self.file_format}}
        # According to documentation, we need to specify sizes in some formats
        if self.file_format != "GIF":
            res["LabelStockSize"] = {"Height": "6", "Width": "4"}
        return res

    def _prepare_create_shipping(self, picking):
        """Return a dict that can be passed to the shipping endpoint of the UPS API"""
        if picking.package_ids:
            packages = [
                self._quant_package_data_from_picking(package, picking, True)
                for package in picking.package_ids
            ]
        else:
            packages = [
                self._quant_package_data_from_picking(
                    self.default_packaging_id, picking, False
                )
            ]
        return {
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

    def _send_shipping(self, picking):
        status = self._process_reply(
            url="%s/ship/v1807/shipments" % self.url,
            data=self._prepare_create_shipping(picking),
        )
        res = status["ShipmentResponse"]["ShipmentResults"]
        if self.carrier.ups_negotiated_rates:
            price = res["ShipmentCharges"]["ServiceOptionsCharges"]
        else:
            price = res["ShipmentCharges"]["TotalCharges"]
        return {
            "price": price,
            "ShipmentIdentificationNumber": res["ShipmentIdentificationNumber"],
            "GraphicImage": res["PackageResults"]["ShippingLabel"]["GraphicImage"],
        }

    def _quant_package_data_from_order(self, order):
        PackageWeight = 0
        DimWeight = 0
        product_length = 0
        width = 0
        height = 0
        for line in order.order_line.filtered(
            lambda x: x.product_id and x.product_id.weight > 0
        ):
            PackageWeight += line.product_id.weight * line.product_uom_qty
        for line in order.order_line.filtered(
            lambda x: x.product_id and x.product_id.volume > 0
        ):
            DimWeight += line.product_id.volume * line.product_uom_qty
            if not DimWeight:
                product_length = self.default_packaging_id.length
                width = self.default_packaging_id.width
                height = self.default_packaging_id.height
        DeclaredValue = ""
        if self.carrier.ups_insurance:
            DeclaredValue = {
                "DeclaredValue": {
                    "CurrencyCode": order.currency_id.name,
                    "MonetaryValue": str(order.amount_untaxed),
                }
            }
        return {
            "PackagingType": {"Code": self.default_packaging_id.shipper_package_code},
            "Dimensions": {
                "UnitOfMeasurement": {"Code": self.package_dimension_code},
                "Length": str(product_length),
                "Width": str(width),
                "Height": str(height),
            },
            "PackageWeight": {
                "UnitOfMeasurement": {"Code": self.package_weight_code},
                "Weight": str(PackageWeight)
                if PackageWeight
                else str(DimWeight / 5000),
            },
            "DimWeight": {
                "UnitOfMeasurement": {"Code": self.package_weight_code},
                "Weight": self._format_dimweight(DimWeight),
            },
            "PackageServiceOptions": DeclaredValue,
        }

    def _prepare_rate_shipment(self, order):
        packages = self._quant_package_data_from_order(order)
        return {
            "RateRequest": {
                "Shipment": {
                    "Shipper": self._partner_to_shipping_data(
                        partner=order.company_id.partner_id,
                        ShipperNumber=self.shipper_number,
                    ),
                    "ShipTo": self._partner_to_shipping_data(order.partner_shipping_id),
                    "ShipFrom": self._partner_to_shipping_data(
                        order.warehouse_id.partner_id
                    ),
                    "Service": {"Code": self.service_code},
                    "Package": packages,
                    "TaxInformationIndicator": "",
                    "ShipmentRatingOptions": {"NegotiatedRatesIndicator": ""},
                }
            }
        }

    def rate_shipment(self, order):
        status = self._process_reply(
            url="%s/ship/v1807/rating/Rate" % self.url,
            data=self._prepare_rate_shipment(order),
        )
        if self.carrier.ups_negotiated_rates:
            if "TotalChargesWithTaxes" in status:
                return status["RateResponse"]["RatedShipment"]["NegotiatedRateCharges"][
                    "TotalChargesWithTaxes"
                ]
            else:
                return status["RateResponse"]["RatedShipment"]["NegotiatedRateCharges"][
                    "TotalCharge"
                ]
        else:
            return status["RateResponse"]["RatedShipment"]["TotalCharges"]

    def _prepare_shipping_label(self, carrier_tracking_ref):
        return {
            "LabelRecoveryRequest": {
                "LabelSpecification": self._label_data(),
                "TrackingNumber": carrier_tracking_ref,
            }
        }

    def shipping_label(self, carrier_tracking_ref):
        res = self._process_reply(
            url="%s/ship/v1807/shipments/labels" % self.url,
            data=self._prepare_shipping_label(carrier_tracking_ref),
        )
        return res["LabelRecoveryResponse"]["LabelResults"]["LabelImage"]

    def cancel_shipment(self, pickings):
        url = "%s/ship/v1/shipments/cancel" % self.url
        for item in pickings.filtered(lambda x: x.carrier_tracking_ref):
            self.url = "{}/{}".format(self.url, item.carrier_tracking_ref)
            self._process_reply(url=url, method="delete")
        return True

    def tracking_state_update(self, picking):
        status = self._process_reply(
            url="%s/track/v1/details/" % self.url,
            method="get",
            query_parameters={"inquiryNumber": picking.carrier_tracking_ref},
        )
        state = False
        for package in status["trackResponse"]["shipment"]["package"]:
            for activity in package["activity"]:
                state = activity["status"]["type"]
        static_states = {
            "I": "in_transit",
            "D": "customer_delivered",
            "E": "incidence",
            "P": "customer_delivered",
            "M": "in_transit",
        }
        return {
            "delivery_state": static_states.get(state, "incidence"),
            "tracking_state_history": state,
        }
