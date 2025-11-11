# Copyright 2025 Manuel Regidor <manuel.regidor@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import requests

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from .cbl_request import CBLRequest


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    delivery_type = fields.Selection(
        selection_add=[("cbl", "CBL")],
        ondelete={
            "cbl": lambda recs: recs.write({"delivery_type": "fixed", "fixed_price": 0})
        },
    )
    cbl_cash_on_delivery = fields.Boolean(
        string="Cash On Delivery",
        help=(
            "If checked, it means that the carrier is paid with cash. It assumes "
            "there is a sale order linked and it will use that "
            "total amount as the value to be paid"
        ),
    )
    cbl_freight_type = fields.Selection(
        string="Freight Type",
        selection=[
            ("D", "Freight Collect"),
            ("P", "Freight Prepaid"),
        ],
        required=True,
        default="D",
    )
    cbl_needs_confirmation = fields.Boolean(
        string="Needs Confirmation",
        help=(
            "If checked, expeditions need to be confirmed after the tracking number is "
            "generated to be officially introduced in CBL pending shipments database."
        ),
    )
    cbl_user = fields.Char(string="User")
    cbl_password = fields.Char(string="Password")
    cbl_client_code = fields.Char(string="Client Code")
    cbl_client_token = fields.Char(string="Client Token")

    cbl_label_format = fields.Selection(
        selection=[("zpl", "ZPL"), ("pdf", "PDF")],
        string="Label Format",
        default="zpl",
        help=(
            "Format to generate shipping labels.\n"
            "If PDF is selected, labels will be generated "
            "using an external service (labelary.com)."
        ),
    )

    @api.model
    def cdl_generate_labels(self, picking, tracking_ref, labels_info):
        labels = []
        attachments = self.env["ir.attachment"]
        label_format = picking.carrier_id.cbl_label_format
        for index, label in enumerate(labels_info):
            zpl = label.get("tag", "")
            if label_format == "pdf":
                url = "http://api.labelary.com/v1/printers/8dpmm/labels/4x6/"
                files = {"file": zpl}
                headers = {"Accept": "application/pdf"}
                response = requests.post(
                    url, headers=headers, files=files, stream=True, timeout=30
                )
                label_content = response.content
                ext = "pdf"
            else:
                label_content = zpl
                ext = "zpl"
            labels.append(
                (
                    "cbl_{}_{}_{}.{}".format(
                        tracking_ref,
                        label.get("sscc", ""),
                        index + 1,
                        ext,
                    ),
                    label_content,
                )
            )
        if labels:
            message = picking.message_post(
                body=_("CBL label(s) created."), attachments=labels
            )
            attachments = message.attachment_ids
        return attachments

    def cbl_send_shipping(self, pickings):
        result = []
        request = CBLRequest(self)
        for picking in pickings:
            tracking_ref, labels = request._send_shipping(picking)
            result.append(
                {
                    "exact_price": 0.0,
                    "tracking_number": tracking_ref,
                }
            )
            if not self.cbl_needs_confirmation:
                picking.write({"cbl_confirmed": True})
            else:
                picking.write({"cbl_confirmed": False})
            if labels:
                self.cdl_generate_labels(picking, tracking_ref, labels)
        return result

    def cbl_cancel_shipment(self, pickings):
        request = CBLRequest(self)
        for picking in pickings.filtered(lambda picking: picking.carrier_tracking_ref):
            tracking_ref = picking.carrier_tracking_ref
            if request.cancel_shipment(picking):
                picking.write({"cbl_confirmed": False})
                msg = _(
                    "CBL Parcel Expedition with reference %(tracking)s cancelled.",
                    tracking=tracking_ref,
                )
                picking.message_post(body=msg)
            else:
                raise UserError(
                    _(
                        "Unable to cancel CBL Expedition with reference "
                        "%(tracking)s. Please, make sure that the reference "
                        "is correct and the expedition has not been already "
                        "canceled.",
                        tracking=tracking_ref,
                    )
                )
        return True

    def cbl_confirm_shipment(self, pickings):
        request = CBLRequest(self)
        for picking in pickings.filtered(
            lambda picking: picking.carrier_tracking_ref
            and not picking.cbl_confirmed
            and picking.delivery_type == "cbl"
        ):
            if request.confirm_shipments(picking):
                picking.write({"cbl_confirmed": True})
                picking.message_post(body=_("CBL Expedition confirmed."))

    def cbl_confirm_shipment_cron(self):
        carriers = self.search(
            [("delivery_type", "=", "cbl"), ("cbl_needs_confirmation", "=", True)]
        )
        for carrier in carriers:
            pickings = self.env["stock.picking"].search(
                [
                    ("carrier_id", "=", carrier.id),
                    ("carrier_tracking_ref", "!=", False),
                    ("cbl_confirmed", "=", False),
                ]
            )
            carrier.cbl_confirm_shipment(pickings)
