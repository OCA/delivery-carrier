# Copyright 2026 Akretion (http://www.akretion.com).
# @author Florian Mounier <florian.mounier@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from base64 import b64encode

from odoo import _, models
from odoo.exceptions import UserError

CUSTOMS_MAP = {
    "gift": "gift",
    "sample": "sample",
    "commercial": "commercial_purpose_or_sale",
    "other": "personal_belongings_or_personal_use",
    "return": "return",
}


class StockQuantPackage(models.Model):
    _inherit = "stock.quant.package"

    def _dhl_express_get_tracking_link(self):
        return (
            "https://www.dhl.com/fr-en/home/tracking.html?tracking-id=%s&submit=1"
            % self.parcel_tracking
        )

    def _dhl_express_should_include_customs(self, picking):
        rv = self._roulier_should_include_customs(picking)
        if not rv and picking.carrier_code in "PYMEH":
            raise UserError(
                _(
                    "Customs declaration is required for Non DOC DHL Express shipments. "
                    "Please check the delivery carrier configuration for picking %s"
                )
                % picking.id
            )
        if rv:
            return rv

    def _dhl_express_before_call(self, picking, payload):
        # For DHL customs are declared at root level
        if self._should_include_customs(picking):
            payload["customs"] = self._get_customs(picking)
        return payload

    def _dhl_express_get_customs(self, picking):
        customs = self._roulier_get_customs(picking)
        for article in customs.get("articles", []):
            article["exportType"] = CUSTOMS_MAP.get(picking.customs_category)

        # We now need the linked invoice for customs declaration
        linked_so = picking.sale_id or picking.move_lines.mapped(
            "sale_line_id.order_id"
        )
        if len(linked_so) != 1:
            raise UserError(
                _(
                    "Cannot determine the sales order linked to picking %s. "
                    "Please make sure there is only one sales order linked to "
                    "the picking for international shipments."
                )
                % picking.id
            )

        if linked_so.invoice_status == "no":
            raise UserError(
                _(
                    "The sales order %s linked to picking %s has no invoice. "
                    "Please make sure there is an invoice linked to the sales order "
                    "for international shipments."
                )
                % (linked_so.id, picking.id)
            )

        # Should we?
        # if linked_so.invoice_status == "to invoice":
        #     new_invoice = linked_so._create_invoices()
        #     new_invoice.action_post()

        invoice = linked_so.invoice_ids.filtered(lambda inv: inv.state == "posted")
        if not invoice:
            raise UserError(
                _(
                    "The sales order %s linked to picking %s has no valid invoice. "
                    "Please make sure there is a valid invoice linked to the sales order "
                    "for international shipments."
                )
                % (linked_so.id, picking.id)
            )

        if len(invoice) > 1:
            raise UserError(
                _(
                    "The sales order %s linked to picking %s has multiple valid invoices. "
                    "Please make sure there is only one valid invoice linked to "
                    "the sales order "
                    "for international shipments."
                )
                % (linked_so.id, picking.id)
            )

        report = self.env.ref("account.account_invoices").with_user(1)
        content, _filename = report._render(
            [invoice.id], {"report_type": report.report_type}
        )

        customs["invoice"] = {
            "number": invoice.name,
            "date": invoice.invoice_date.isoformat(),
            "content": b64encode(content),
        }

        customs["vat"] = invoice.amount_tax
        # delivery, insurance?

        return customs

    def _dhl_express_get_parcel(self, picking):
        return {
            **self._roulier_get_parcel(picking),
            "length": self.pack_length,
            "width": self.width,
            "height": self.height,
        }
