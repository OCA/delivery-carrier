# Copyright 2020 Hunki Enterprises BV
# Copyright 2021 Tecnativa - Víctor Martínez
# Copyright 2024 Sygel - Manuel Regidor
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import datetime
import logging

import requests

from odoo import _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class UpsRequest(object):
    def __init__(self, carrier):
        self.carrier = carrier
        self.default_packaging_id = self.carrier.ups_default_packaging_id
        self.use_packages_from_picking = self.carrier.ups_use_packages_from_picking
        self.shipper_number = self.carrier.ups_shipper_number
        self.service_code = self.carrier.ups_service_code
        self.file_format = self.carrier.ups_file_format
        self.package_dimension_code = self.carrier.ups_package_dimension_code
        self.package_weight_code = self.carrier.ups_package_weight_code
        self.transaction_src = "Odoo (%s)" % self.carrier.name
        self.client_id = self.carrier.ups_client_id
        self.client_secret = self.carrier.ups_client_secret
        self.token = self.carrier.ups_token
        self.token_expiration_date = self.carrier.ups_token_expiration_date
        self.url = "https://wwwcie.ups.com"
        if self.carrier.prod_environment:
            self.url = "https://onlinetools.ups.com"

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

    def _send_request(
        self, url, json=None, data=None, headers=None, method="post", auth=None
    ):
        return getattr(requests, method)(
            url, data=data, json=json, headers=headers, auth=auth
        )

    def _get_new_token(self):
        if not (self.client_id and self.client_secret):
            raise UserError(
                _(
                    "Both Client ID and Client Secret must be set in UPS delivery carriers."
                )
            )
        url = "%s/security/v1/oauth/token" % self.url
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
    ):
        if (
            not self.token
            or not self.token_expiration_date
            or (self.token_expiration_date <= datetime.datetime.now())
        ):
            self._get_new_token()
        data = data or {}
        headers = {
            "Authorization": "Bearer {}".format(self.token),
        }
        if headers_extra:
            headers = {**headers, **headers_extra}
        status = self._send_request(url, json, data, headers, method)
        # Generate a new token
        if status.status_code == 401:
            self._get_new_token()
            status = self._send_request(url, json, data, headers, method)
        status = status.json()
        ups_last_request = ("URL: {}\nData: {}").format(self.url, data)
        self.carrier.log_xml(ups_last_request, "ups_last_request")
        self.carrier.log_xml(status or "", "ups_last_response")
        return status

    def _quant_package_data_from_picking(self, package, picking, is_package=False):
        NumOfPieces = picking.number_of_packages
        PackageWeight = picking.shipping_weight
        if is_package:
            NumOfPieces = sum(package.mapped("quant_ids.quantity"))
            PackageWeight = max(package.shipping_weight, package.weight)
            package = package.packaging_id
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
            # modelo: stock.quant.package
            packages = [
                self._quant_package_data_from_picking(package, picking, True)
                for package in picking.package_ids
            ]
        else:
            # modelo: product.packaging
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
        return vals

    def _send_shipping(self, picking):
        status = self._process_reply(
            url="%s/api/shipments/v1/ship" % self.url,
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
        return {
            "price": res["ShipmentCharges"]["TotalCharges"],
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
            url="%s/api/rating/v1/Rate" % self.url,
            json=self._prepare_rate_shipment(order),
        )
        self._raise_for_status(status, skip_errors)
        return status

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
            url="%s/api/labels/v1/recovery" % self.url,
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
        url = "%s/api/shipments/v1/void/cancel" % self.url
        url = "{}/{}".format(url, picking.carrier_tracking_ref)
        status = self._process_reply(url=url, method="delete")
        self._raise_for_status(status, False)
        return True

    def tracking_state_update(self, picking):
        static_states = {
            "I": "in_transit",
            "D": "customer_delivered",
            "E": "incidence",
            "P": "customer_delivered",
            "M": "in_transit",
        }
        status = self._process_reply(
            url="%s/api/track/v1/details/%s" % (self.url, picking.carrier_tracking_ref),
            method="get",
            headers_extra={
                "transId": "{}".format(datetime.datetime.now().timestamp()),
                "transactionSrc": "{} - Odoo".format(picking.company_id.name),
            },
        )
        self._raise_for_status(status, False)
        states_list = []
        delivery_state = "incidence"
        try:
            shipment = status["trackResponse"]["shipment"][0]
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
                        "incidence",
                    )
            else:
                for warning in shipment.get("warnings"):
                    states_list.append(
                        _("{} - Warning: {}").format(
                            datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            warning.get("message"),
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
        }
