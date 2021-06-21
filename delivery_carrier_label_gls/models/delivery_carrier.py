# -*- coding: utf-8 -*-
# Copyright 2021 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    delivery_type = fields.Selection(selection_add=[("gls", "Gls")])

    gls_contact_id = fields.Char(string="Contact ID")
    gls_login = fields.Char(string="Login User", group="base.group_system")
    gls_password = fields.Char(string="Login Password", group="base.group_system")
    gls_url = fields.Char(string="Service Url", group="base.group_system")
    gls_url_test = fields.Char(string="Test Service Url", group="base.group_system")
    gls_url_tracking = fields.Char(
        help="Root URL for parcel tracking. Needs a %s for the tracking reference."
    )
    gls_label_format = fields.Selection(
        string="Label format",
        selection=[
            ("pdf", "PDF"),
            ("zebra", "Zebra"),
            ("intermec", "Intermec"),
            ("datamax", "Datamax"),
            ("toshiba", "Toshiba"),
        ],
        default="pdf",
    )
    gls_label_template = fields.Selection(
        string="Label Template",
        selection=[
            ("D_200", "D200"),
            ("PF_4_I", "PF4I"),
            ("PF_4_I_200", "PF4I200"),
            ("PF_4_I_300", "PF4I300"),
            ("PF_8_D_200", "PF8D200"),
            ("T_200_BF", "T200BF"),
            ("T_300_BF", "T300BF"),
            ("ZPL_200", "ZPL200"),
            ("ZPL_300", "ZPL300"),
        ],
        default=False,
    )

    @api.constrains(
        "delivery_type",
        "gls_contact_id",
        "gls_login",
        "gls_password",
        "gls_url_tracking",
        "gls_label_format",
    )
    def _check_gls_fields(self):
        gls_field_names = [
            "gls_contact_id",
            "gls_login",
            "gls_password",
            "gls_url_tracking",
        ]
        gls_records = self.filtered(lambda c: c.delivery_type == "gls")
        for rec in gls_records:
            for field_name in gls_field_names + ["gls_label_format"]:
                value = rec[field_name]
                if not value:
                    field = rec._fields[field_name]
                    description_string = field._description_string(self.env)
                    msg = _("The GLS field '%s' is required for carrier %s")
                    raise ValidationError(msg % (description_string, rec.name))
                if field_name == "gls_url_tracking" and "%s" not in value:
                    raise ValidationError(_("The tracking url must contain '%s'."))
        for rec in self - gls_records:
            if any(rec[f] for f in gls_field_names):
                msg = _("Incorrect GLS parameters set on carrier %s.")
                raise ValidationError(msg % rec.name)

    @api.constrains("delivery_type", "prod_environment", "gls_url", "gls_url_test")
    def _check_gls_url(self):
        gls_records = self.filtered(lambda c: c.delivery_type == "gls")
        for rec in gls_records:
            if not rec.prod_environment and not rec.gls_url_test:
                msg = _("The GLS field 'Test Service Url' is required in test mode.")
                raise ValidationError(msg)
            if rec.prod_environment and not rec.gls_url:
                msg = _("The GLS field 'Service Url' is required in production mode.")
                raise ValidationError(msg)
        for rec in self - gls_records:
            if rec.gls_url or rec.gls_url_test:
                msg = _("Incorrect GLS parameters set on carrier %s.")
                raise ValidationError(msg % rec.name)

    def gls_get_shipping_price_from_so(self, order):
        self.ensure_one()
        return [0]  # TODO?

    def gls_send_shipping(self, picking):
        tracking_number = picking.gls_send_shipping(self)
        return [{"exact_price": False, "tracking_number": tracking_number}]

    @api.model
    def gls_tracking_url(self, tracking_number):
        return self.gls_url_tracking % tracking_number

    def gls_get_tracking_link(self, pickings):
        links = []
        for picking in pickings:
            for link in picking.mapped("package_ids.parcel_tracking"):
                if link:
                    links.append(self.gls_tracking_url(link))
        return links

    def gls_cancel_shipment(self, pickings):
        if pickings.mapped("package_ids.report_id"):
            msg = _("Packages cannot be cancelled after the End of Day report.")
            raise ValidationError(msg)
        for picking in pickings:
            picking.gls_cancel_shipment()

    def _get_gls_client(self):
        """Return a GLS connection client using this carrier configuration."""
        # the client checks all parameters, so nothing needed here.
        self.ensure_one()
        return self.env["delivery.client.gls"].create({"carrier_id": self.id})
