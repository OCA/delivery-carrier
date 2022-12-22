# Copyright 2021 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    delivery_type = fields.Selection(
        selection_add=[("gls", "GLS")],
        ondelete={
            "gls": lambda recs: recs.write({"delivery_type": "fixed", "fixed_price": 0})
        },
    )

    gls_contact_id = fields.Char(
        string="International",
        size=10,
        help="Contact id for GLS International transportation (T8914)",
    )
    gls_url = fields.Char(string="Service Url")
    gls_url_test = fields.Char(string="Test Service Url")
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
    gls_return_partner_id = fields.Many2one(
        "res.partner",
        string="Return Address",
        help="If set, this partner's address will be used on the return label.",
    )

    @api.constrains("gls_return_partner_id")
    def _check_gls_return_partner_id(self):
        records_to_check = self.filtered(
            lambda c: c.delivery_type == "gls" and c.gls_return_partner_id
        )
        for carrier in records_to_check:
            carrier.gls_return_partner_id._gls_prepare_address()

    @api.constrains(
        "delivery_type",
        "gls_contact_id",
        "gls_url_tracking",
        "gls_label_format",
        "carrier_account_id",
    )
    def _check_gls_fields(self):
        gls_field_names = [
            "gls_contact_id",
            "gls_url_tracking",
            "gls_label_format",
            "carrier_account_id",
        ]
        gls_records = self.filtered(lambda c: c.delivery_type == "gls")
        for rec in gls_records:
            for field_name in gls_field_names:
                value = rec[field_name]
                if not value:
                    field = rec._fields[field_name]
                    description_string = field._description_string(self.env)
                    raise ValidationError(
                        _(
                            f"The GLS field '{description_string}' is required for "
                            f"carrier {rec.name}"
                        )
                    )

        for rec in self - gls_records:
            if any(
                rec[f]
                for f in gls_field_names
                if f not in ("carrier_account_id", "gls_label_format")
            ):
                raise ValidationError(
                    _(f"Incorrect GLS parameters set on carrier {rec.name}.")
                )

    @api.constrains("delivery_type", "prod_environment", "gls_url", "gls_url_test")
    def _check_gls_url(self):
        for rec in self.filtered(lambda c: c.delivery_type == "gls"):
            if not rec.prod_environment and not rec.gls_url_test:
                raise ValidationError(
                    _("The GLS field 'Test Service Url' is required in test mode")
                )
            if rec.prod_environment and not rec.gls_url:
                raise ValidationError(
                    _("The GLS field 'Service Url' is required in non test mode")
                )

    def gls_send_shipping(self, picking):
        tracking_number = picking.gls_send_shipping(self)
        return [{"exact_price": False, "tracking_number": tracking_number}]

    @api.model
    def gls_tracking_url(self, tracking_number):
        return self.gls_url_tracking % tracking_number

    def gls_get_tracking_link(self, pickings):
        links = []
        for picking in pickings:
            for link in picking.package_ids.parcel_tracking:
                if link:
                    links.append(self.gls_tracking_url(link))
        return links

    def gls_cancel_shipment(self, pickings):
        if pickings.package_ids.report_id:
            msg = _("Packages cannot be canceled after the End of Day report.")
            raise ValidationError(msg)
        for picking in pickings:
            picking.gls_cancel_shipment()

    def _get_gls_client(self):
        """Return a GLS connection client using this carrier configuration."""
        # the client checks all parameters, so nothing needed here.
        self.ensure_one()
        return self.env["delivery.client.gls"].create({"carrier_id": self.id})
