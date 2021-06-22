# coding: utf-8
# Copyright 2021 ACSONE SA/NV
# © 2015 David BEAL @ Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class StockQuantPackage(models.Model):
    _inherit = "stock.quant.package"

    carrier_id = fields.Many2one("delivery.carrier")
    report_id = fields.Many2one(
        "delivery.report.gls", "GLS Delivery Report", readonly=True, copy=False
    )
    gls_package_ref = fields.Char("GLS Identifier", readonly=True, copy=False)
    gls_picking_id = fields.Many2one(
        comodel_name="stock.picking",
        string="Picking used in GLS",
        readonly=True,
        copy=False,
    )

    def gls_cancel_shipment(self):
        self.ensure_one()
        if not self.parcel_tracking:
            raise ValidationError(
                _("You cannot cancel a pack that wasn't sent to GLS.")
            )
        client = self.carrier_id._get_gls_client()
        client.cancel_parcel(self.parcel_tracking)
        self.parcel_tracking = False
        self.gls_package_ref = False
        label = self.env["shipping.label"].search([("package_id", "=", self.id)])
        label.attachment_id.unlink()
        label.unlink()

    def _get_carrier_tracking_url(self):
        url = None
        if self.carrier_id.delivery_type == "gls" and self.parcel_tracking:
            url = self.carrier_id.gls_tracking_url(self.parcel_tracking)
        return url

    def open_tracking_url(self):
        self.ensure_one()
        url = self._get_carrier_tracking_url()
        if not url:
            raise UserError(_("Cannot open tracking URL for this carrier."))
        return {"type": "ir.actions.act_url", "url": url, "target": "new"}

    def gls_validate_package(self):
        self.ensure_one()
        package_name = self.name or self.id
        allowed_product_types = ["PARCEL", "EXPRESS", "FREIGHT"]
        if self.packaging_id.shipper_package_code not in allowed_product_types:
            msg = _("The GLS package code for package %s should be in %s.")
            raise ValidationError(msg % (package_name, allowed_product_types))
        if not self.gls_picking_id:
            msg = _("The GLS picking is missing on package %s.")
            raise ValidationError(msg % package_name)
        if not self.shipping_weight:
            msg = _("The shipping weight is missing on package %s.")
            raise ValidationError(msg % package_name)

    def gls_send_shipping_package(self):
        self.ensure_one()
        self.gls_validate_package()
        client = self.carrier_id._get_gls_client()
        weight = max(self.shipping_weight, 0.1)  # GLS API requirement
        shipment = {
            "Product": self.packaging_id.shipper_package_code,
            "Consignee": {"Address": self._gls_prepare_address()},
            "ShipmentUnit": [{"Weight": "{:05.2f}".format(weight)}],
            "ShipmentReference": [self.gls_picking_id.name or "PICKING%s" % self.id],
            "Service": self._gls_prepare_package_service(),
        }
        response = client.create_parcel({"Shipment": shipment})

        assert len(response["CreatedShipment"]["ParcelData"]) == 1  # :-/
        parcel_data = response["CreatedShipment"]["ParcelData"][0]
        tracking = parcel_data["TrackID"]
        # !! if you don't want to pay for lost API calls, you need:
        # https://github.com/odoo/odoo/pull/54321/
        self.env.cr.after("rollback", lambda: client.cancel_parcel(tracking))
        self.parcel_tracking = tracking
        self.gls_package_ref = parcel_data["ParcelNumber"]
        label_content = response["CreatedShipment"]["PrintData"]
        self._gls_label_package(label_content)

    def _gls_prepare_address(self):
        self.ensure_one()
        address_payload = {}
        mapping = {
            "name": "Name1",
            "street": "Street",
            "city": "City",
            "email": "eMail",
            "zip": "ZIPCode",
            "phone": "FixedLinePhonenumber",
            "country_id.code": "CountryCode",
            "state_id.name": "Province",
        }
        mapping_optional = {"phone", "state_id.name"}
        partner = self.gls_picking_id.partner_id
        for key in mapping:
            if "." in key:
                value = partner.mapped(key)
                value = value[0] if value else value
            else:
                value = partner[key]
            if not value and key not in mapping_optional:
                msg = _("Missing required parameter %s on partner %s")
                raise ValidationError(msg % (key, partner.name))
            if value:
                address_payload[mapping[key]] = value
        return address_payload

    @api.model
    def _gls_prepare_package_service(self):
        if not self.gls_picking_id.gls_parcel_shop:
            service = [{"Service": {"ServiceName": "service_flexdelivery"}}]
        else:
            details = {
                "ServiceName": "service_shopdelivery",
                "ParcelShopID": self.gls_picking_id.gls_parcel_shop,
            }
            service = [{"ShopDelivery": details}]
        return service

    @api.model
    def _gls_label_package(self, label_data):
        self.ensure_one()
        extension = "pdf" if self.carrier_id.gls_label_format == "pdf" else "txt"
        file_type = self.carrier_id.gls_label_format
        name = (self.name or "PACKAGE%s" % self.id) + "." + extension
        vals_label = {
            "package_id": self.id,
            "datas": label_data[0]["Data"],
            "datas_fname": name,
            "res_id": self.gls_picking_id.id,
            "res_model": self.gls_picking_id._name,
            "file_type": file_type,
            "type": "binary",
            "name": name,
        }
        return self.env["shipping.label"].create(vals_label)
