# Copyright 2022 Tecnativa - Víctor Martínez
# Copyright 2026 Nitrokey GmbH
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import _, api, fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    ups_landed_cost_quote_identifier = fields.Char(
        string="UPS Global Checkout Quote ID",
        help="Quote ID from UPS Global Checkout, copied from the sale order. It is "
        "sent to UPS at shipment creation so the guaranteed duties and taxes are "
        "linked to this shipment. Clear it to ship without DDP, or set an existing "
        "Quote ID to enforce DDP on a manually created delivery order.",
        copy=False,
    )
    ups_global_checkout_reason_for_export = fields.Selection(
        selection=[
            ("SALE", "Sale"),
            ("GIFT", "Gift"),
            ("SAMPLE", "Sample"),
            ("RETURN", "Return"),
            ("REPAIR", "Repair"),
            ("INTERCOMPANYDATA", "Intercompany Data"),
        ],
        string="UPS Reason for Export",
        default="SALE",
        help="Reason for export sent on the customs invoice (InternationalForms) "
        "for this UPS Global Checkout shipment.",
    )

    @api.model_create_multi
    def create(self, vals_list):
        """Copy the UPS Global Checkout Quote ID from the originating sale order."""
        pickings = super().create(vals_list)
        for picking in pickings:
            if (
                picking.carrier_id.delivery_type == "ups"
                and not picking.ups_landed_cost_quote_identifier
                and picking.sale_id.ups_landed_cost_quote_identifier
            ):
                picking.ups_landed_cost_quote_identifier = (
                    picking.sale_id.ups_landed_cost_quote_identifier
                )
        return pickings

    def send_to_shipper(self):
        res = super().send_to_shipper()
        order = self.sale_id
        # Only report duties when DDP was actually applied to the shipment. The
        # shipment builder clears the picking Quote ID when the landed cost line
        # was removed, so it is the source of truth for "DDP applied".
        if (
            self.carrier_id.delivery_type == "ups"
            and self.ups_landed_cost_quote_identifier
            and order.ups_landed_cost_amount
        ):
            self.message_post(
                body=_(
                    "UPS Global Checkout Duties, Taxes & Fees: "
                    "%(amount).2f %(currency)s",
                    amount=order.ups_landed_cost_amount,
                    currency=order.currency_id.name,
                )
            )
        return res

    def ups_get_label(self):
        self.ensure_one()
        tracking_ref = self.carrier_tracking_ref
        if self.delivery_type != "ups" or not tracking_ref:
            return
        return self.carrier_id.ups_get_label(tracking_ref)
