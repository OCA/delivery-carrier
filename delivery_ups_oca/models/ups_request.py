# Copyright 2020 Hunki Enterprises BV
# Copyright 2021 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import logging

import requests

from odoo import _, fields

_logger = logging.getLogger(__name__)

UPS_API_URL = {
    "test": "https://onlinetools.ups.com",
    "prod": "https://wwwcie.ups.com",
}
UPS_API_SERVICE = {
    "shipping": "/ship/v1807/shipments",
    "label": "/ship/v1807/shipments/labels",
    "cancel": "/ship/v1/shipments/cancel",
    "status": "/track/v1/details/",
    "rate": "/ship/v1807/rating/Rate",
}


class UpsRequest:
    def __init__(self, prod=False, service="shipping", params=None):
        self.access_license_number = params.get("access_license_number")
        self.username = params.get("username")
        self.password = params.get("password")
        self.default_packaging_id = params.get("default_packaging_id")
        self.shipper_number = params.get("shipper_number")
        self.service_code = params.get("service_code")
        self.file_format = params.get("file_format")
        self.package_dimension_code = params.get("package_dimension_code")
        self.package_weight_code = params.get("package_weight_code")
        self.transaction_src = params.get("transaction_src")
        api_env = "prod" if prod else "test"
        self.url = UPS_API_URL[api_env] + UPS_API_SERVICE[service]

    def _process_reply(
        self, payload=None, method="post", query_parameters=None,
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
            self.url, json=payload, headers=headers, params=query_parameters
        ).json()
        errors = status.get("response", {}).get("errors")
        if errors:
            _logger.info(
                _("Sending to UPS: %s")
                % ("\n".join("%(code)s %(message)s" % error for error in errors),)
            )
        return status

    def _quant_package_data_from_picking(self, package, picking, is_package=True):
        NumOfPieces = picking.number_of_packages
        PackageWeight = picking.shipping_weight
        if is_package:
            NumOfPieces = sum(package.mapped("quant_ids.quantity"))
            PackageWeight = package.weight
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
                "Weight": str(PackageWeight),
            },
            "PackageServiceOptions": "",
        }

    def _partner_to_shipping_data(self, partner, **kwargs):
        """Return a dict describing a partner for the shipping request"""
        return dict(
            **kwargs,
            Name=(partner.parent_id or partner).name,
            AttentionName=partner.name,
            TaxIdentificationNumber=partner.vat,
            Phone=dict(Number=partner.phone or partner.mobile),
            EMailAddress=partner.email,
            Address=dict(
                AddressLine=[partner.street, partner.street2 or ""],
                City=partner.city,
                StateProvinceCode=partner.state_id.code,
                PostalCode=partner.zip,
                CountryCode=partner.country_id.code,
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
        status = self._process_reply(payload=self._prepare_create_shipping(picking))
        res = status["ShipmentResponse"]["ShipmentResults"]
        price = self._get_response_price(
            res["ShipmentCharges"]["TotalCharges"],
            picking.company_id.currency_id,
            picking.company_id,
        )
        return {
            "price": price,
            "ShipmentIdentificationNumber": res["ShipmentIdentificationNumber"],
            "GraphicImage": res["PackageResults"]["ShippingLabel"]["GraphicImage"],
        }

    def _get_response_price(self, total_charges, currency, company):
        price = float(total_charges["MonetaryValue"])
        if total_charges["CurrencyCode"] != currency.name:
            price = currency._convert(
                price,
                self.env["res.currency"].search(
                    [("name", "=", total_charges["CurrencyCode"])]
                ),
                company,
                fields.Date.today(),
            )
        return price

    def _quant_package_data_from_order(self, order):
        PackageWeight = 0
        for product in order.order_line.filtered(
            lambda x: x.product_id and x.product_id.weight > 0
        ):
            PackageWeight += product.product_id.weight
        return {
            "PackagingType": {"Code": self.default_packaging_id.shipper_package_code},
            "Dimensions": {
                "UnitOfMeasurement": {"Code": self.package_dimension_code},
                "Length": str(self.default_packaging_id.length),
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
                }
            }
        }

    def rate_shipment(self, order):
        status = self._process_reply(payload=self._prepare_rate_shipment(order))
        return self._get_response_price(
            status["RateResponse"]["RatedShipment"]["TotalCharges"],
            order.currency_id,
            order.company_id,
        )

    def _prepare_shipping_label(self, carrier_tracking_ref):
        return {
            "LabelRecoveryRequest": {
                "LabelSpecification": self._label_data(),
                "TrackingNumber": carrier_tracking_ref,
            }
        }

    def shipping_label(self, carrier_tracking_ref):
        res = self._process_reply(
            payload=self._prepare_shipping_label(carrier_tracking_ref)
        )
        return res["LabelRecoveryResponse"]["LabelResults"]["LabelImage"]

    def cancel_shipment(self, pickings):
        for item in pickings.filtered(lambda x: x.carrier_tracking_ref):
            self.url = "{}/{}".format(self.url, item.carrier_tracking_ref)
            self._process_reply(method="delete")
        return True

    def tracking_state_update(self, picking):
        status = self._process_reply(
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
