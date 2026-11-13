# Copyright 2025 Tecnativa - Víctor Martínez
# Copyright 2026 Acysos S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import base64

from odoo import _, fields, models
from odoo.exceptions import UserError


class DachserTransferListWizard(models.TransientModel):
    _name = "dachser.transfer.list.wizard"
    _description = "Dachser Daily Loading Manifest (Transfer List) Download Wizard"

    carrier_id = fields.Many2one(
        comodel_name="delivery.carrier",
        string="Dachser Delivery Method",
        required=True,
        domain="[('delivery_type', '=', 'dachser')]",
    )
    order_date = fields.Date(
        string="Order Date (Transfer List)",
        required=True,
        default=fields.Date.context_today,
    )
    order_group = fields.Char(
        string="Order Group (Optional)",
        help="Filter the loading manifest by a specific order group in eLogistics.",
    )
    pdf_file = fields.Binary(
        string="Manifest PDF",
        readonly=True,
    )
    pdf_filename = fields.Char(
        string="Filename",
        readonly=True,
    )

    def action_download_transfer_list(self):
        self.ensure_one()
        client = self.carrier_id._dachser_get_client()
        date_str = fields.Date.to_string(self.order_date)
        resp = client.get_transfer_list(
            order_date=date_str,
            order_group=(
                self.order_group or self.carrier_id.dachser_order_group or None
            ),
        )
        doc_b64 = resp.get("document") or resp.get("transferList") or resp.get("label")
        if not doc_b64:
            raise UserError(
                _("Dachser did not return any PDF manifest for date %s.") % date_str
            )
        filename = f"Dachser_Manifest_{date_str}.pdf"
        self.write(
            {
                "pdf_file": doc_b64.encode("ascii")
                if isinstance(doc_b64, str)
                else base64.b64encode(doc_b64),
                "pdf_filename": filename,
            }
        )
        return {
            "type": "ir.actions.act_window",
            "res_model": "dachser.transfer.list.wizard",
            "res_id": self.id,
            "view_mode": "form",
            "target": "new",
        }
