# Copyright 2024 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import Command, _, models
from odoo.exceptions import UserError


class IrActionsReport(models.Model):
    _inherit = "ir.actions.report"

    def print_document(self, record_ids, data=None):
        if (
            self.report_name
            != "stock_picking_delivery_label_to_printer.report_shipping_label"
        ):
            return super().print_document(record_ids, data)
        return self.print_shipping_label(record_ids, data)

    def print_shipping_label(self, res_ids, data):
        behaviour = self.behaviour()
        printer = behaviour.pop("printer", None)
        can_print_report = behaviour["action"] == "server" and printer
        shipping_label_ids = data.get("shipping_label_ids")
        if not can_print_report or not shipping_label_ids:
            # Maybe we could trigger the download...
            raise UserError(_("Labels can only be printed with CUPS"))
        print_attachment = self.env["wizard.print.attachment"].create(
            {
                "printer_id": printer.id,
                "attachment_line_ids": [
                    Command.create({"attachment_id": attachment})
                    for attachment in shipping_label_ids
                ],
            }
        )
        print_attachment.print_attachments()
        # This might be untrue!
        return True

    def _render_qweb_pdf(self, res_ids=None, data=None):
        if (
            self.report_name
            != "stock_picking_delivery_label_to_printer.report_shipping_label"
        ):
            return super()._render_qweb_pdf(res_ids, data)
        return self.print_shipping_label(res_ids, data)
