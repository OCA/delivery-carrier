# Copyright 2025 Tecnativa - Víctor Martínez
# Copyright 2026 Acysos S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models

from .dachser_master_data import DACHSER_DELIVERY_NOTICE_TYPES


class ResPartner(models.Model):
    _inherit = "res.partner"

    dachser_partner_id = fields.Char(
        string="Dachser Partner ID",
        copy=False,
        help="8-digit customer/consignee identifier assigned by Dachser (optional).",
    )
    dachser_gln = fields.Char(
        string="GLN Code (Dachser)",
        copy=False,
        size=13,
        help="13-digit Global Location Number for EDI/API identification in Dachser.",
    )
    dachser_tail_lift = fields.Boolean(
        string="Requires Tail-Lift (Dachser)",
        default=False,
        help=(
            "Check if the consignee requires a truck with a tail-lift on "
            "Dachser deliveries."
        ),
    )
    dachser_delivery_notice_type = fields.Selection(
        selection=DACHSER_DELIVERY_NOTICE_TYPES,
        string="Dachser Delivery Notice",
        default="none",
        help=(
            "Delivery pre-notice preference for the consignee "
            "(by phone or electronic)."
        ),
    )
