# Copyright 2025 Tecnativa - Víctor Martínez
# Copyright 2026 Acysos S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import base64

from odoo import _, fields, models
from odoo.exceptions import UserError

from ..models.dachser_request import DachserRequest


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

    def _process_transfer_list_dachser(self, doc_b64):
        date_str = fields.Date.to_string(self.order_date)
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

    def _process_transfer_list_custom(self, items):
        manifest_data = []
        picking_model = self.env["stock.picking"]
        for item in items:
            ref = item["id"]
            picking = picking_model.search(
                [
                    ("carrier_id", "=", self.carrier_id.id),
                    ("carrier_tracking_ref", "=", ref),
                ],
                limit=1,
            )
            if not picking:
                raise UserError(
                    self.env._("No picking has been found with the reference %s") % ref,
                )
            manifest_data.append(picking._dachser_report_manifest_data())
        datas = {
            "ids": self.env.context.get("active_ids", []),
            "deliveries": manifest_data,
            "model": self._name,
            "order_date": self.order_date,
            "company_name": self.env.company.name,
        }
        return (
            self.env.ref("delivery_dachser.dachser_manifest_report")
            .with_context(landscape=True)
            .report_action(self, data=datas)
        )

    def action_download_transfer_list(self):
        self.ensure_one()
        carrier = self.carrier_id
        client = DachserRequest(carrier)
        date_str = fields.Date.to_string(self.order_date)
        resp = client.get_transfer_list(
            order_date=date_str,
            order_group=(self.order_group or carrier.dachser_order_group or None),
        )
        report_type = carrier.dachser_manifest_report_type
        if report_type == "dachser":
            resp = resp.get("document") or resp.get("transferList") or resp.get("label")
        if not resp:
            raise UserError(
                _("Dachser did not return any PDF manifest for date %s.") % date_str
            )
        method_name = f"_process_transfer_list_{report_type}"
        return getattr(self, method_name)(resp)
