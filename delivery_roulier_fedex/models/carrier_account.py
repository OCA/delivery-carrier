#  Copyright (c) 2026 Groupe Voltaire
#  @author Emilie SOUTIRAS  <emilie.soutiras@groupevoltaire.com>
#  License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

PDF_LABEL_STOCK_TYPES = [
    ("PAPER_4X6", "Paper 4x6"),
    ("PAPER_4X675", "Paper 4x6.75"),
    ("PAPER_85X11_TOP_HALF_LABEL", "Paper 8.5x11 top half"),
    ("PAPER_85X11_BOTTOM_HALF_LABEL", "Paper 8.5x11 bottom half"),
]
THERMAL_LABEL_STOCK_TYPES = [
    ("STOCK_4X6", "Thermal 4x6"),
    ("STOCK_4X675", "Thermal 4x6.75"),
    ("STOCK_4X675_LEADING_DOC_TAB", "Thermal 4x6.75 leading doc tab"),
    ("STOCK_4X675_TRAILING_DOC_TAB", "Thermal 4x6.75 trailing doc tab"),
]
DOC_TAB_LABEL_STOCK_TYPES = (
    "STOCK_4X675_LEADING_DOC_TAB",
    "STOCK_4X675_TRAILING_DOC_TAB",
)


class CarrierAccount(models.Model):
    _inherit = "carrier.account"

    fedex_rest_account_number = fields.Char(
        string="FedEx Account Number",
        help="FedEx shipping account number (9 digits). "
        "The API Key and Secret Key of the FedEx Developer Portal project "
        "go in the 'Account Number' and 'Account Password' fields.",
    )
    fedex_rest_file_format = fields.Selection(
        [("PDF", "PDF"), ("ZPLII", "ZPL II"), ("PNG", "PNG")],
        string="FedEx File Format",
        default="PDF",
    )
    fedex_rest_label_stock_type = fields.Selection(
        PDF_LABEL_STOCK_TYPES + THERMAL_LABEL_STOCK_TYPES,
        string="FedEx Label Stock Type",
        default="PAPER_4X6",
        help="Only these stock types are eligible to the FedEx "
        "Simple Label Certification.",
    )
    fedex_rest_doc_tab_content_type = fields.Selection(
        [("STANDARD", "Standard"), ("MINIMUM", "Minimum")],
        string="FedEx Doc Tab Content",
        default="STANDARD",
        help="Content printed on the detachable doc tab of thermal "
        "doc tab label stocks.",
    )
    fedex_rest_pickup_type = fields.Selection(
        [
            ("USE_SCHEDULED_PICKUP", "Regular scheduled pickup"),
            ("CONTACT_FEDEX_TO_SCHEDULE", "Contact FedEx to schedule a pickup"),
            ("DROPOFF_AT_FEDEX_LOCATION", "Drop-off at a FedEx location"),
        ],
        string="FedEx Pickup Type",
        default="USE_SCHEDULED_PICKUP",
    )
    fedex_rest_duties_payment_type = fields.Selection(
        [("SENDER", "Sender"), ("RECIPIENT", "Recipient")],
        string="FedEx Duties Paid By",
        default="SENDER",
    )
    fedex_rest_use_etd = fields.Boolean(
        string="FedEx Electronic Trade Documents",
        help="Let FedEx generate and transmit the commercial invoice "
        "electronically for shipments requiring customs clearance.",
    )

    fedex_rest_notify_recipient = fields.Boolean(
        string="FedEx Email Notifications",
        help="Let FedEx email the tracking number and the shipment progress "
        "to the recipient of the shipment.",
    )
    fedex_rest_notify_on_shipment = fields.Boolean(
        string="Notify on Shipment",
        default=True,
        help="Email sent when the shipment is created.",
    )
    fedex_rest_notify_on_tender = fields.Boolean(
        string="Notify on Tender",
        help="Email sent when the shipment is tendered to FedEx.",
    )
    fedex_rest_notify_on_estimated_delivery = fields.Boolean(
        string="Notify on Estimated Delivery",
    )
    fedex_rest_notify_on_exception = fields.Boolean(
        string="Notify on Exception",
        default=True,
    )
    fedex_rest_notify_on_delivery = fields.Boolean(
        string="Notify on Delivery",
        default=True,
    )
    fedex_rest_notification_message = fields.Char(
        string="FedEx Notification Message",
        help="Personal message added to the FedEx notification emails.",
    )

    def _fedex_rest_get_notification_events(self):
        self.ensure_one()
        return [
            event
            for event, enabled in (
                ("ON_SHIPMENT", self.fedex_rest_notify_on_shipment),
                ("ON_TENDER", self.fedex_rest_notify_on_tender),
                (
                    "ON_ESTIMATED_DELIVERY",
                    self.fedex_rest_notify_on_estimated_delivery,
                ),
                ("ON_EXCEPTION", self.fedex_rest_notify_on_exception),
                ("ON_DELIVERY", self.fedex_rest_notify_on_delivery),
            )
            if enabled
        ]

    @api.constrains(
        "delivery_type",
        "fedex_rest_notify_recipient",
        "fedex_rest_notify_on_shipment",
        "fedex_rest_notify_on_tender",
        "fedex_rest_notify_on_estimated_delivery",
        "fedex_rest_notify_on_exception",
        "fedex_rest_notify_on_delivery",
    )
    def _check_fedex_rest_notification_events(self):
        for account in self.filtered(
            lambda a: a.delivery_type == "fedex_rest" and a.fedex_rest_notify_recipient
        ):
            if not account._fedex_rest_get_notification_events():
                raise ValidationError(
                    _(
                        "Select at least one event for the FedEx email "
                        "notifications of the carrier account %s.",
                        account.name,
                    )
                )

    @api.constrains(
        "delivery_type", "fedex_rest_file_format", "fedex_rest_label_stock_type"
    )
    def _check_fedex_rest_label_stock_type(self):
        pdf_stock_types = {code for code, _label in PDF_LABEL_STOCK_TYPES}
        for account in self.filtered(lambda a: a.delivery_type == "fedex_rest"):
            is_paper = account.fedex_rest_label_stock_type in pdf_stock_types
            if is_paper != (account.fedex_rest_file_format in ("PDF", "PNG")):
                raise ValidationError(
                    _(
                        "FedEx label stock type %(stock)s is not compatible "
                        "with the %(format)s file format.",
                        stock=account.fedex_rest_label_stock_type,
                        format=account.fedex_rest_file_format,
                    )
                )
