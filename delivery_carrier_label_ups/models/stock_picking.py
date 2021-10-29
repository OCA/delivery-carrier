# Copyright 2020 Hunki Enterprises BV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import logging

import requests

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _inherit = "stock.picking"

    @api.depends(
        'delivery_type', 'location_id.usage', 'carrier_tracking_ref', 'state'
    )
    def _compute_show_label_button(self):
        """Show the label button for returns via UPS in any active state to allow
        users requesting an ERL when it fits their workflow"""
        for this in self:
            if this.delivery_type == 'ups' and this.location_id.usage == 'customer':
                this.show_label_button = (
                    not this.carrier_tracking_ref and
                    this.state not in ('done', 'cancel')
                )
            else:
                super(StockPicking, this)._compute_show_label_button()

    def generate_shipping_labels(self):
        """Generate labels on button click"""
        self.ensure_one()
        if self.carrier_id.delivery_type != "ups":
            return super().generate_shipping_labels()
        result = []
        for package in self._get_packages_from_picking():
            status = self._ups_request("label", self._ups_label_data(package))
            self._ups_raise_error(status)
            label_results = status["LabelRecoveryResponse"]["LabelResults"]
            result.append(
                {
                    "name": package.name,
                    "file": label_results["LabelImage"]["GraphicImage"],
                    "file_type": label_results["LabelImage"]["LabelImageFormat"][
                        "Code"
                    ].lower(),
                    "tracking_number": label_results["TrackingNumber"],
                }
            )
        return result

    def _ups_send(self, force=False):
        """Send packages of the picking to UPS
        return a list of dicts {'exact_price': 'tracking_number':}
        suitable for delivery.carrier#send_shipping"""
        result = []
        self._ups_check_picking_consistency()
        for this in self:
            if this.carrier_tracking_ref and not force:
                result.append({
                    "exact_price": 0,
                    "tracking_number": this.carrier_tracking_ref,
                })
                continue
            this._set_a_default_package()
            status = this._ups_request_shipping()
            total_charges = status["ShipmentResponse"]["ShipmentResults"][
                "ShipmentCharges"
            ]["TotalCharges"]
            price = float(total_charges["MonetaryValue"])
            if total_charges["CurrencyCode"] != this.company_id.currency_id.name:
                price = this.company_id.currency_id._convert(
                    price,
                    self.env["res.currency"].search(
                        [("name", "=", total_charges["CurrencyCode"])]
                    ),
                    this.company_id,
                    fields.Date.today(),
                )
            this._ups_set_parcel_tracking(status)

            # this api also can return a label immediately,
            # so we write it here immediately
            if self.env.context.get("get_parcel_labels"):
                shipping_labels = this._ups_get_parcel_labels(status)
                for label in shipping_labels:
                    this.attach_shipping_label(label)

            result.append(
                {
                    "exact_price": price,
                    "tracking_number": status["ShipmentResponse"]["ShipmentResults"][
                        "ShipmentIdentificationNumber"
                    ],
                }
            )
        return result

    def _ups_get_parcel_labels(self, status):
        """ Retrieve labels data from ShipmentResponse """
        self.ensure_one()
        shipping_labels = []
        package_results = status["ShipmentResponse"]["ShipmentResults"][
            "PackageResults"
        ]
        if isinstance(package_results, dict):
            package_results = [package_results]
        for package_result in package_results:
            shipping_labels.append(
                {
                    "name": package_result["TrackingNumber"],
                    "file": package_result["ShippingLabel"]["GraphicImage"],
                    "file_type": package_result["ShippingLabel"]["ImageFormat"][
                        "Code"
                    ].lower(),
                    "tracking_number": package_result["TrackingNumber"],
                }
            )
        return shipping_labels

    def _ups_set_parcel_tracking(self, status):
        """ Upon receiving Tracking Number and Tracking URL from UPS,
        set them in packages """
        self.ensure_one()
        # the api returns a dict when we have one package, and a list for multiple
        package_results = status["ShipmentResponse"]["ShipmentResults"][
            "PackageResults"
        ]
        packages = self._ups_get_picking_parcels()
        if isinstance(package_results, dict):
            package_results = [package_results]
        for package, package_result in zip(packages, package_results):
            package.write(
                {
                    "parcel_tracking": package_result["TrackingNumber"],
                    "parcel_tracking_uri": self._ups_tracking_url(
                        package_result["TrackingNumber"]
                    ),
                }
            )

    def _ups_get_picking_parcels(self):
        """ Get packages to be sent to UPS """
        self.ensure_one()
        return self.package_ids

    def _ups_request_shipping(self):
        """ Send shipping request to UPS """
        self.ensure_one()
        shipping_data = self._ups_shipping_data()
        res = self._ups_request("shipping", shipping_data)
        self._ups_raise_error(res)
        return res

    def _ups_check_picking_consistency(self):
        """ Check that picking has one shipping option """
        for this in self:
            if len(this.option_ids) != 1:
                raise UserError(
                    _("Picking %s must set exactly one shipping option") % this.name
                )

    def _ups_cancel(self):
        """Cancel shipping"""
        # note UPS also supports cancelling specific packages in a shipping,
        # but that's not what we do here
        for this in self:
            status = this._ups_request(
                "cancel", method="delete", url_parameters=(this.carrier_tracking_ref,)
            )
            this._ups_raise_error(status)

    def _ups_shipping_data(self):
        """Return a dict that can be passed to the shipping endpoint of the UPS API"""
        self.ensure_one()
        account = self._ups_auth_account()
        shipping_data = dict(
            ShipTo=self._ups_partner_to_shipping_data(self.partner_id),
            ShipFrom=self._ups_partner_to_shipping_data(
                self.picking_type_id.warehouse_id.partner_id
            ),
            Service=dict(
                Code=self.option_ids[:1].code,
                Description=self.option_ids[:1].name,
            ),
        )
        if self.location_id.usage == 'customer':
            # this is a return, so issue a pickup order and swap to/from
            shipping_data.update(
                ShipTo=shipping_data.pop('ShipFrom'),
                ShipFrom=shipping_data.pop('ShipTo'),
            )
            shipping_data.update(self._ups_return_service())
        result = dict(
            ShipmentRequest=dict(
                Shipment=dict(
                    Description=self._ups_reference(),
                    Shipper=self._ups_partner_to_shipping_data(
                        self.company_id.partner_id,
                        ShipperNumber=account.ups_shipper_number,
                    ),
                    PaymentInformation=dict(
                        ShipmentCharge=dict(
                            Type="01",
                            BillShipper=dict(
                                # we ignore the alternatives paying per credit card or
                                # paypal for now
                                AccountNumber=account.ups_shipper_number,
                            ),
                        )
                    ),
                    Package=self._ups_order_data_product(),
                    **shipping_data,
                ),
                LabelSpecification=self._ups_label_specification(account),
            )
        )
        if self.env.context.get("enable_negotiated_rates"):
            # Enable negotiated rates
            result['ShipmentRequest']['Shipment'].update(
                ShipmentRatingOptions=dict(NegotiatedRatesIndicator="")
            )
        return result

    def _ups_order_data_product(self):
        """Return a dict describing all the packages for the shipping request"""
        return [
            self._ups_quant_package_data(package)
            for package in self.package_ids
        ]

    def _ups_return_service(self):
        """Return a dict describing the UPS Return Label code"""
        self.ensure_one()
        customer_email = self.partner_id.email
        warehouse_partner = self.picking_type_id.warehouse_id.partner_id
        warehouse_partner_email = warehouse_partner.email
        if self.partner_id.country_id.code != 'US':
            subject_code = '01'  # First shipment reference
        else:
            subject_code = '03'  # First package reference

        return dict(
            ReturnService=dict(
                # UPS Electronic Return Label (ERL)
                Code='8',
            ),
            ShipmentServiceOptions=dict(
                LabelDelivery=dict(
                    EMailMessage=dict(
                        EMailAddress=customer_email,
                        FromEMailAddress=warehouse_partner_email,
                        SubjectCode=subject_code,
                    )
                ),
                Notification=[
                    dict(
                        NotificationCode='2',
                        EMail=dict(
                            EMailAddress=customer_email,
                            UndeliverableEMailAddress=warehouse_partner_email,
                            FromEMailAddress=warehouse_partner_email,
                        ),
                    ),
                    dict(
                        NotificationCode='5',
                        EMail=dict(
                            EMailAddress=customer_email,
                            FromEMailAddress=warehouse_partner_email,
                        ),
                    ),
                    dict(
                        NotificationCode='7',
                        EMail=dict(
                            EMailAddress=customer_email,
                            FromEMailAddress=warehouse_partner_email,
                        ),
                    ),
                    dict(
                        NotificationCode='8',
                        EMail=dict(
                            EMailAddress=customer_email,
                            UndeliverableEMailAddress=warehouse_partner_email,
                            FromEMailAddress=warehouse_partner_email,
                        ),
                    )
                ]
            ),
        )

    def _ups_partner_to_shipping_data(self, partner, **kwargs):
        """Return a dict describing a partner for the shipping request"""
        return dict(
            **kwargs,
            Name=(partner.parent_id or partner).name,
            AttentionName=partner.name,
            TaxIdentificationNumber=partner.vat,
            Phone=dict(Number=partner.phone or partner.mobile,),
            EMailAddress=partner.email,
            Address=dict(
                AddressLine=[partner.street, partner.street2],
                City=partner.city,
                StateProvinceCode=partner.state_id.code,
                PostalCode=partner.zip,
                CountryCode=partner.country_id.code,
            ),
        )

    def _ups_quant_package_data(self, package):
        """Return a dict describing a package for the shipping request"""
        get_param = self.env["ir.config_parameter"].sudo().get_param
        weight_uom = (
            int(get_param("product.weight_in_lbs", 0,))
            and "LBS"
            or "KGS"
        )
        dimension_uom = (
            int(get_param("product.weight_in_lbs", 0,))
            and "IN"
            or "CM"
        )
        return dict(
            Description=package.name,
            NumOfPieces=str(sum(package.mapped("quant_ids.quantity"))),
            Packaging=dict(
                # fall back to 'Customer supplied package' if unset
                Code=package.packaging_id.ups_code or "02",
                Description=package.packaging_id.name or "Custom",
            ),
            Dimensions=dict(
                UnitOfMeasurement=dict(Code=dimension_uom),
                Length=str(package.packaging_id.length),
                Width=str(package.packaging_id.width),
                Height=str(package.packaging_id.height),
            ),
            PackageWeight=dict(
                UnitOfMeasurement=dict(Code=weight_uom,),
                Weight=str(package.shipping_weight or package.weight),
            ),
            PackageServiceOptions="",
        )

    def _ups_label_data(self, package):
        """Return a dict that can be passed to the label endpoint of the UPS API"""
        self.ensure_one()
        account = self._ups_auth_account()
        return dict(
            LabelRecoveryRequest=dict(
                LabelSpecification=self._ups_label_specification(account),
                # TODO we could add a Translate key here to translate to a few languages
                TrackingNumber=package.parcel_tracking,
            ),
        )

    def _ups_label_specification(self, account):
        """Return a dict containing the UPS Label Specification"""
        return dict(
            LabelImageFormat=dict(Code="GIF", ),
            LabelPrintMethod=dict(Code=account.file_format or "PDF", ),
        )

    def _ups_raise_error(self, api_result):
        """If UPS' API returned an error, raise it"""
        errors = api_result.get("response", {}).get("errors")
        if errors:
            raise UserError(
                _("Sending %s to UPS: %s")
                % (
                    self.name,
                    "\n".join("%(code)s %(message)s" % error for error in errors),
                )
            )

    def _ups_request(
        self,
        request_type,
        payload=None,
        method="post",
        url_parameters=None,
        query_parameters=None,
    ):
        """Send a request to one of the UPS endpoints"""
        self.ensure_one()
        account = self._ups_auth_account()
        if not account:
            raise UserError(_("No UPS account found for this company"))
        url = self.env["ir.config_parameter"].sudo().get_param(
            "delivery_carrier_label_ups.%s_%s"
            % (
                request_type,
                self.carrier_id.prod_environment and "production" or "test",
            )
        ) % (url_parameters or ())
        headers = {
            "AccessLicenseNumber": account.ups_access_license,
            "Username": account.account,
            "Password": account.password,
            "transactionSrc": "Odoo (%s)" % self.env.cr.dbname,
        }
        return getattr(requests, method)(
            url, json=payload, headers=headers, params=query_parameters
        ).json()

    def _ups_auth_account(self):
        """Find a carrier.account matching our carrier"""
        self.ensure_one()
        return self.env["carrier.account"].search(
            [
                ("delivery_type", "=", "ups"),
                "|",
                ("company_id", "=", False),
                ("company_id", "=", self.company_id.id),
            ],
            limit=1,
            order="company_id desc",
        )

    def _ups_reference(self):
        """Return a reference for this picking to be passed to UPS"""
        self.ensure_one()
        return self.name

    def _ups_tracking_url(self, tracking_number):
        """Return an URL for a tracking number"""
        return "https://ups.com/WebTracking/track?trackingNumber=%s" % tracking_number
