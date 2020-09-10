# Copyright 2020 Hunki Enterprises BV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import base64
import hashlib
import logging

import zeep

from odoo import _, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def action_generate_carrier_label(self):
        # do nothing for paazl pickings as we have created the labels
        # during send already
        return super(
            StockPicking, self.filtered(lambda x: x.carrier_id.delivery_type != "paazl")
        ).action_generate_carrier_label()

    def _paazl_send(self):
        """Register this picking and commit to paazl immediately,
        return a list of dicts {'exact_price': 'tracking_number':}
        suitable for delivery.carrier#send_shipping"""
        result = []
        api = self._paazl_api()
        for this in self:
            this._set_a_default_package()
            status = api.service.order(**this._paazl_order_data())
            if status.error and status.error.code == 1003:
                # this order has been sent already, so we update it
                status = api.service.updateOrder(**this._paazl_order_data())
            this._paazl_raise_error(status)
            status = api.service.commitOrder(**this._paazl_commit_order_data())
            if status.error and status.error.code != 1003:
                this._paazl_raise_error(status)
            # we need to create labels in order to get a tracking number
            status = api.service.generateLabels(**this._paazl_generate_labels_data())
            this._paazl_raise_error(status)
            # as we have the labels anyways, attach them
            self.env["shipping.label"].create(
                this.get_shipping_label_values(
                    {
                        "name": this.name,
                        "file": base64.b64encode(status.labels),
                        "file_type": status.labels[:4] == b"%PDF" and "pdf" or "zpl",
                    }
                )
            )
            result.append(
                {
                    # TODO to get this right, we'd have to request shipping options
                    # and find the price of the shipping option selected
                    "exact_price": 0,
                    "tracking_number": status.metaData[0]["trackingNumber"],
                }
            )
        return result

    def _paazl_cancel(self):
        """Cancel a shipment"""
        api = self._paazl_api()
        for this in self:
            auth_order_id = this._paazl_auth_order_id()
            status = api.service.cancelShipments(
                webshop=auth_order_id.pop("webshop"), label=auth_order_id,
            )
            this._paazl_raise_error(status)

    def _paazl_api(self):
        """Return a soap client with the correct url"""
        # TODO use caching for the wsdl
        production = all(self.mapped("carrier_id.prod_environment"))
        wsdl = self.env["ir.config_parameter"].get_param(
            "delivery_carrier_label_paazl.wsdl_%s"
            % (production and "production" or "test")
        )
        return zeep.Client(wsdl)

    def _paazl_raise_error(self, api_result):
        """If paazl's API returned an error, raise it"""
        if api_result.error:
            raise UserError(
                _("Sending %s to paazl: %s %s")
                % (self.name, api_result.error.code, api_result.error.message,)
            )

    def _paazl_order_data(self):
        """Return a dict that can be passed as parameters to the `order`
        endpoint of the paazl soap api"""
        self.ensure_one()
        return dict(
            **self._paazl_auth_order_id(),
            products=dict(
                product=[
                    self._paazl_quant_to_order_data(quant)
                    for package in self.package_ids
                    for quant in package.quant_ids
                ]
            ),
        )

    def _paazl_quant_to_order_data(self, quant):
        """Return a dict describing a quant for the `order` endpoint"""
        result = {
            "quantity": int(quant.quantity),
            "weight": quant.product_id.weight,
            "volume": quant.product_id.volume,
            "code": quant.product_id.default_code,
            "description": quant.product_id.description_pickingout or "/",
            "hsTariffCode": quant.product_id.hs_code,
        }
        # support product_dimension if installed
        for name in ["length", "height", "width"]:
            field_name = "product_%s" % name
            if field_name not in quant.product_id._fields:
                continue
            result[name] = quant.product_id[field_name]
            uom = quant.product_id.dimensional_uom_id
            if uom:
                result[name] = uom._compute_quantity(
                    result[name], self.env.ref("uom.product_uom_cm"),
                )
            result[name] = int(result[name])
        return result

    def _paazl_commit_order_data(self):
        """Return a dict that can be passed as parameters to the `commitOrder`
        endpoint of the paazl soap api"""
        self.ensure_one()
        shipping_address = self._paazl_partner_to_order_data(self.partner_id)
        shipping_address["customerName"] = shipping_address.pop("addresseeLine")
        if self.partner_id.parent_id:
            shipping_address["companyName"] = self.partner_id.parent_id.name
        return dict(
            **self._paazl_auth_order_id(),
            pendingOrderReference=self._paazl_reference(),
            customerEmail=self.partner_id.email,
            customerPhoneNumber=self.partner_id.phone,
            shippingMethod=dict(
                type="delivery",
                identifier=0,
                # TODO should we validate that there's exacly one option set?
                option=self.option_ids[:1].code,
                orderWeight=sum(
                    product["quantity"] * product["weight"]
                    for product in self._paazl_order_data()["products"]["product"]
                ),
                description=self.note or "/",
                packageCount=len(self.package_ids),
            ),
            shipperAddress=self._paazl_partner_to_order_data(
                self.picking_type_id.warehouse_id.partner_id,
            ),
            shippingAddress=shipping_address,
            totalAmount=0,
        )

    def _paazl_partner_to_order_data(self, partner):
        """Return a dict describing a partner for the `commitOrder` endpoint"""
        result = {
            "addresseeLine": partner.name,
            "street": partner.street,
            "housenumber": "",
            "zipcode": partner.zip,
            "city": partner.city,
            "province": partner.state_id.code,
            "country": partner.country_id.code,
        }
        # support base_address_extended if installed
        if "street_name" in partner._fields:
            result.update(
                street=partner.street_name, housenumber=partner.street_number,
            )
        return result

    def _paazl_generate_labels_data(self):
        """Return a dict to be passed to the generateLabels endpoint"""
        self.ensure_one()
        auth_order_id = self._paazl_auth_order_id()
        account = self._paazl_auth_account()
        return {
            "webshop": auth_order_id.pop("webshop"),
            "labelFormat": account.file_format or "PDF",
            "order": auth_order_id,
            "includeMetaData": True,
        }

    def _paazl_auth_account(self):
        """Find a carrier.account matching our carrier"""
        self.ensure_one()
        return self.env["carrier.account"].search(
            [
                ("delivery_type", "=", "paazl"),
                "|",
                ("company_id", "=", False),
                ("company_id", "=", self.company_id.id),
            ],
            limit=1,
        )

    def _paazl_auth_order_id(self, reference_name=None):
        """Return a dict of hash, webshop and order reference used
        by paazl to authenticate a SOAP API call"""
        self.ensure_one()
        account = self._paazl_auth_account()
        if not account:
            raise UserError(_("No paazl account found for this company"))
        return {
            "hash": hashlib.sha1(
                (account.account + account.password + self._paazl_reference()).encode()
            ).hexdigest(),
            "webshop": account.account,
            reference_name or "orderReference": self._paazl_reference(),
        }

    def _paazl_reference(self):
        """Return a reference for a picking to be used for paazl"""
        self.ensure_one()
        return self.name
