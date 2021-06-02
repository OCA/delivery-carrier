# Copyright 2020 Hunki Enterprises BV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import base64
import hashlib
import logging

import zeep

from odoo import _, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _inherit = "stock.picking"

    paazl_carrier_tracking_url = fields.Char()

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
        self._paazl_check_picking_consistency()
        self._set_a_default_package()
        result = []
        for this in self:
            this._paazl_send_update_order()
            result.append(this._paazl_generate_labels())
        return result

    def _paazl_check_picking_consistency(self):
        """ Check consistency of picking data before sending to Paazl """
        for this in self:
            if len(this.option_ids) != 1:
                raise UserError(
                    _("Picking %s must set exactly one shipping option") % this.name
                )

    def _paazl_send_update_order(self, change_order=False):
        """ Create Paazl order or update it if already existing """
        self.ensure_one()
        api = self._paazl_api()
        status = api.service.order(**self._paazl_order_data())
        if status.error and status.error.code == 1003:
            # this order has been sent already, so we update it
            status = api.service.updateOrder(**self._paazl_order_data())
        self._paazl_raise_error(status)
        status = api.service.commitOrder(**self._paazl_commit_order_data())
        if change_order:
            if status.error and status.error.code == 1003:
                status = api.service.changeOrder(**self._paazl_change_order_data())
            self._paazl_raise_error(status)
        elif status.error and status.error.code != 1003:
            self._paazl_raise_error(status)

    def _paazl_generate_labels(self):
        """ Generate Paazl labels.
        return dict {'exact_price': 'tracking_number':}
        """
        self.ensure_one()
        api = self._paazl_api()
        # we need to create labels in order to get a tracking number
        status = api.service.generateLabels(**self._paazl_generate_labels_data())
        self._paazl_raise_error(status)
        # as we have the labels anyways, attach them
        account = self._get_carrier_account()
        file_type = (account.file_format or "").lower() or "pdf"
        label = {
            "name": self._paazl_reference(),
            "file": base64.b64encode(status.labels),
            "filename": "{}.{}".format(self._paazl_reference(), file_type),
            "file_type": file_type,
        }
        return {
            # TODO to get this right, we'd have to request shipping options
            # and find the price of the shipping option selected
            "exact_price": 0,
            "tracking_number": self._paazl_get_tracking_number(status),
            "labels": [label],
        }

    def _paazl_cancel(self):
        """Cancel a shipment"""
        api = self._paazl_api()
        for this in self:
            auth_order_id = this._paazl_auth_order_id()
            status = api.service.cancelShipments(
                webshop=auth_order_id.pop("webshop"), label=auth_order_id,
            )
            this._paazl_raise_error(status)

    def _paazl_get_tracking_number(self, status):
        """Return the tracking number that is passed in the status"""
        return status.metaData[0]['trackingNumber']

    def _paazl_get_tracking_link(self):
        """Return the tracking link if we got it already"""
        return self.paazl_carrier_tracking_url

    def _paazl_api(self):
        """Return a soap client with the correct url"""
        # TODO use caching for the wsdl
        production = all(self.mapped("carrier_id.prod_environment"))
        wsdl = self.env["ir.config_parameter"].sudo().get_param(
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
                product=self._paazl_order_data_product()
            ),
        )

    def _paazl_order_data_product(self):
        """ Format the products parameter to be sent to the `order`
        endpoint of the paazl soap api"""
        self.ensure_one()
        # use packages if they have packaging set, otherwise products
        use_products = not any(self.mapped('package_ids.packaging_id'))
        return [
            self._paazl_quant_to_order_data(quant)
            for package in self.package_ids
            for quant in package.quant_ids
        ] if use_products else [
            self._paazl_package_to_order_data(package)
            for package in self.package_ids
        ]

    def _paazl_quant_to_order_data(self, quant):
        """Return a dict describing a quant for the `order` endpoint"""
        result = {
            "quantity": int(quant.quantity),
            "weight": quant.product_id.weight,
            "volume": quant.product_id.volume,
            "code": quant.product_id.default_code or "",
            "description": (quant.product_id.description_pickingout
                            or quant.product_id.name),
            "hsTariffCode": quant.product_id.hs_code or "",
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

    def _paazl_package_to_order_data(self, package):
        """Return a dict describing a package for the `order` endpoint"""
        packaging = package.packaging_id
        # choose a product to represent the whole package for product specific
        # values. It depends on the carrier if we actually need that
        products = package.mapped('quant_ids.product_id')
        product = products.filtered('hs_code')[:1] or products[:1]
        return {
            "quantity": 1,
            "weight": package.shipping_weight or package.weight,
            "volume": packaging.width * packaging.height * packaging.length,
            "width": packaging.width,
            "height": packaging.height,
            "length": packaging.length,
            "code": product.default_code or "",
            "description": product.description_pickingout or product.name,
            "hsTariffCode": product.hs_code or "",
        }

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
                option=self.option_ids[:1].code,
                orderWeight=sum(
                    product["quantity"] * product["weight"]
                    for product in self._paazl_order_data()["products"]["product"]
                ),
                description=self.note or "/",
                packageCount=self._paazl_package_count(),
            ),
            shipperAddress=self._paazl_partner_to_order_data(
                self.picking_type_id.warehouse_id.partner_id,
            ),
            shippingAddress=shipping_address,
            totalAmount=0,
        )

    def _paazl_change_order_data(self):
        """Return a dict that can be passed as parameters to the `changeOrder`
        endpoint of the paazl soap api"""
        res = self._paazl_commit_order_data()
        res.pop("pendingOrderReference")
        res.update(self._paazl_order_data())
        return res

    def _paazl_package_count(self):
        """ Return the number of the packages"""
        self.ensure_one()
        return len(self.package_ids)

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
                street=partner.street_name,
                housenumber=partner.street_number,
                addition=partner.street_number2,
            )
        return result

    def _paazl_generate_labels_data(self):
        """Return a dict to be passed to the generateLabels endpoint"""
        self.ensure_one()
        auth_order_id = self._paazl_auth_order_id()
        account = self._get_carrier_account()
        return {
            "webshop": auth_order_id.pop("webshop"),
            "labelFormat": account.file_format or "PDF",
            "order": auth_order_id,
            "includeMetaData": True,
        }

    def _paazl_auth_order_id(self, reference_name=None):
        """Return a dict of hash, webshop and order reference used
        by paazl to authenticate a SOAP API call"""
        self.ensure_one()
        account = self._get_carrier_account()
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
