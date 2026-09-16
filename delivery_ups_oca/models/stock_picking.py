# Copyright 2022 Tecnativa - Víctor Martínez
# Copyright 2025 Nitrokey GmbH
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import ast
import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _inherit = "stock.picking"

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

    @api.model_create_multi
    def create(self, vals_list):
        """Override to set ups_paperless_auto_send based on country group"""
        pickings = super().create(vals_list)
        for picking in pickings:
            if picking._get_ups_paperless_auto_send():
                picking.ups_paperless_auto_send = True
        return pickings

    def button_validate(self):
        """Override to trigger paperless documents upload when validating a picking"""
        res = super().button_validate()
        for picking in self:
            if (
                picking.carrier_id
                and picking.carrier_id.delivery_type == "ups"
                and picking.ups_paperless_auto_send
                and not picking.ups_document_identifier
                and picking.ups_paperless_document_ids
            ):
                try:
                    picking.carrier_id.send_ups_paperless_documents(picking)
                except Exception as e:
                    # Log the error but don't block the validation
                    self.env.user.notify_warning(
                        message=f"Failed to send paperless documents: {str(e)}",
                        title="UPS Paperless Documents",
                        sticky=True,
                    )
        return res
