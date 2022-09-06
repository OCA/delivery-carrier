# Copyright 2020 Hunki Enterprises BV
# Copyright 2021 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import logging

import requests

from odoo import _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class UpsRequest(object):
    def __init__(self, carrier):
        self.carrier = carrier
        self.access_license_number = self.carrier.ups_access_license
        self.username = self.carrier.ups_ws_username
        self.password = self.carrier.ups_ws_password
        self.default_packaging_id = self.carrier.ups_default_package_type_id
        self.use_packages_from_picking = self.carrier.ups_use_packages_from_picking
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
        return status

    def _raise_for_status(self, status, skip_errors=True):
        errors = status.get("response", {}).get("errors")
        if errors:
            msg = _("Sending to UPS: %s") % (
                "\n".join("%(code)s %(message)s" % error for error in errors),
            )
            if skip_errors:
                _logger.info(msg)
            else:
                raise UserError(msg)

    def _quant_package_data_from_picking(self, package_type, picking, is_package=True):
        NumOfPieces = picking.number_of_packages
        PackageWeight = picking.shipping_weight
        if is_package:
            NumOfPieces = len(picking.package_ids)
            PackageWeight = sum(picking.mapped('package_ids.shipping_weight') or [0.0])
        return {
            "Description": package_type.name,
            "NumOfPieces": str(NumOfPieces),
            "Packaging": {
                "Code": package_type.shipper_package_code,
                "Description": package_type.name,
            },
            "Dimensions": {
                "UnitOfMeasurement": {"Code": self.package_dimension_code},
                "Length": str(package_type.packaging_length),
                "Width": str(package_type.width),
                "Height": str(package_type.height),
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
        if self.use_packages_from_picking and picking.package_ids:
            packages = [
                self._quant_package_data_from_picking(package, picking, True)
                for package in picking.package_ids
            ]
        else:
            packages = []
            package_info = self._quant_package_data_from_picking(
                self.default_packaging_id, picking, False
            )
            package_weight = round(
                (picking.shipping_weight / picking.number_of_packages), 2
            )
            for i in range(0, picking.number_of_packages):
                package_item = package_info
                package_name = "%s (%s)" % (picking.name, i + 1)
                package_item["Description"] = package_name
                package_item["NumOfPieces"] = "1"
                package_item["Packaging"]["Description"] = package_name
                package_item["PackageWeight"]["Weight"] = str(package_weight)
                packages.append(package_item)
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

    def _send_shipping(self, picking):
        status = self._process_reply(
            url="%s/ship/v1807/shipments" % self.url,
            data=self._prepare_create_shipping(picking),
        )
        self._raise_for_status(status, False)
        res = status["ShipmentResponse"]["ShipmentResults"]
        PackageResults = res["PackageResults"]
        if not isinstance(PackageResults, list):
            PackageResults = [PackageResults]
        return {
            "price": res["ShipmentCharges"]["TotalCharges"],
            "ShipmentIdentificationNumber": res["ShipmentIdentificationNumber"],
            "PackageResults": PackageResults,
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
        return {
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

    def _rate_shipment(self, order, skip_errors=False):
        status = self._process_reply(
            url="%s/ship/v1807/rating/Rate" % self.url,
            data=self._prepare_rate_shipment(order),
        )
        self._raise_for_status(status, skip_errors)
        return status

    def test_call(self, order):
        res = self._rate_shipment(order, True)
        return res["response"] if "response" in res else res

    def rate_shipment(self, order):
        status = self._rate_shipment(order)
        return status["RateResponse"]["RatedShipment"]["TotalCharges"]

    def _prepare_shipping_label(self, carrier_tracking_ref):
        return {
            "LabelRecoveryRequest": {
                "LabelSpecification": self._label_data(),
                "TrackingNumber": carrier_tracking_ref,
            }
        }

    def shipping_label(self, carrier_tracking_ref):
        status = self._process_reply(
            url="%s/ship/v1807/shipments/labels" % self.url,
            data=self._prepare_shipping_label(carrier_tracking_ref),
        )
        self._raise_for_status(status, False)
        return status["LabelRecoveryResponse"]["LabelResults"]["LabelImage"]

    def cancel_shipment(self, pickings):
        url = "%s/ship/v1/shipments/cancel" % self.url
        for item in pickings.filtered(lambda x: x.carrier_tracking_ref):
            self.url = "{}/{}".format(self.url, item.carrier_tracking_ref)
            status = self._process_reply(url=url, method="delete")
            self._raise_for_status(status, False)
        return True

    def tracking_state_update(self, picking):
        status = self._process_reply(
            url="%s/track/v1/details/" % self.url,
            method="get",
            query_parameters={"inquiryNumber": picking.carrier_tracking_ref},
        )
        self._raise_for_status(status, False)
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
