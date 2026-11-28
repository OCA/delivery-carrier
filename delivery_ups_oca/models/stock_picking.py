# Copyright 2022 Tecnativa - Víctor Martínez
# Copyright 2025 Nitrokey GmbH
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import ast
import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _inherit = "stock.picking"

    declared_value_currency_id = fields.Many2one(
        comodel_name="res.currency",
        string="Declared Value Currency",
        compute="_compute_declared_value_currency_id",
        store=True,
        readonly=True,
    )
    declared_value = fields.Monetary(
        currency_field="declared_value_currency_id",
        compute="_compute_declared_value",
        store=True,
        readonly=False,
        help="Declared value for shipping insurance.",
    )

    @api.depends(
        "sale_id", "sale_id.currency_id", "company_id", "company_id.currency_id"
    )
    def _compute_declared_value_currency_id(self):
        for picking in self:
            if picking.sale_id and picking.sale_id.currency_id:
                picking.declared_value_currency_id = picking.sale_id.currency_id
            else:
                picking.declared_value_currency_id = picking.company_id.currency_id

    def _get_declared_value_base_amount(self):
        self.ensure_one()
        if not self.sale_id:
            return 0.0
        total = 0.0
        for move in self.move_ids:
            sale_line = move.sale_line_id
            if not sale_line or not sale_line.product_uom_qty:
                continue
            unit_price = sale_line.price_total / sale_line.product_uom_qty
            total += unit_price * move.quantity
        return total

    @api.depends(
        "sale_id",
        "move_ids.quantity",
        "move_ids.sale_line_id.price_total",
        "move_ids.sale_line_id.product_uom_qty",
        "carrier_id",
    )
    def _compute_declared_value(self):
        for picking in self:
            picking.declared_value = picking._get_declared_value_base_amount() * (
                picking.carrier_id.declared_value_percentage / 100.0
            )

    ups_document_identifier = fields.Char(
        "DocumentID",
        help="Comma separated Forms History Document IDs, one per uploaded form",
        readonly=True,
        copy=False,
    )
    ups_paperless_document_ids = fields.One2many(
        "ups.paperless.document", "ups_stock_picking_id", string="Paperless Document"
    )
    ups_paperless_auto_send = fields.Boolean(
        string="Automatically Send",
        help="True if you need to send UPS Paperless Documents",
    )

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
        """Set ups_paperless_auto_send based on country group and copy the UPS
        Global Checkout Quote ID from the originating sale order."""
        pickings = super().create(vals_list)
        for picking in pickings:
            if picking._get_ups_paperless_auto_send():
                picking.ups_paperless_auto_send = True
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
        elif (
            self.carrier_id.delivery_type == "ups"
            and self.carrier_id.ups_landed_cost_estimate_ddp
            and order.ups_landed_cost_estimate_amount
            and order.order_line.filtered("is_ups_landed_cost_estimate")
        ):
            self.message_post(
                body=_(
                    "UPS Landed Cost Duties, Taxes & Fees (DDP): "
                    "%(amount).2f %(currency)s",
                    amount=order.ups_landed_cost_estimate_amount,
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

    def generate_paperless_documents(self):
        return self.carrier_id.send_ups_paperless_documents(self)

    def _get_ups_document_ids(self):
        self.ensure_one()
        identifier = (self.ups_document_identifier or "").strip()
        if not identifier:
            return []
        if identifier.startswith("["):
            try:
                identifier = ",".join(ast.literal_eval(identifier))
            except (ValueError, SyntaxError, TypeError):
                _logger.warning(
                    "Could not parse UPS document identifier %s", identifier
                )
        return [doc_id.strip() for doc_id in identifier.split(",") if doc_id.strip()]

    def _get_ups_paperless_auto_send(self):
        self.ensure_one()
        return bool(
            self.carrier_id.delivery_type == "ups"
            and self.partner_id
            and self.partner_id.country_id
            in self.carrier_id.ups_paperless_country_group_ids.mapped("country_ids")
        )

    @api.onchange("carrier_id", "partner_id")
    def _onchange_ups_paperless_auto_send(self):
        for rec in self:
            rec.ups_paperless_auto_send = rec._get_ups_paperless_auto_send()

    def button_validate(self):
        """Override to trigger paperless documents upload when validating a picking

        A failing upload blocks the validation of the whole batch.
        """
        res = super().button_validate()
        for picking in self:
            # The validation may have returned a wizard instead of validating
            if (
                picking.state == "done"
                and picking.carrier_id
                and picking.carrier_id.delivery_type == "ups"
                and picking.ups_paperless_auto_send
                and not picking.ups_document_identifier
                and picking.ups_paperless_document_ids
            ):
                try:
                    picking.carrier_id.send_ups_paperless_documents(picking)
                except Exception as e:
                    message = _(
                        "Failed to send UPS Paperless Documents: %s",
                        str(e) or type(e).__name__,
                    )
                    _logger.error(message)
                    raise UserError(message) from e
        return res
