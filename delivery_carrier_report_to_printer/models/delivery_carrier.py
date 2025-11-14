# Copyright 2025 Tecnativa - Carlos Lopez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command, fields, models


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    label_report_id = fields.Many2one(
        comodel_name="ir.actions.report",
        domain=[("model", "=", "delivery.carrier")],
    )

    def send_shipping(self, pickings):
        if not self.label_report_id or self.env.context.get("skip_label_printing"):
            return super().send_shipping(pickings)
        domain = [("res_id", "in", pickings.ids), ("res_model", "=", pickings._name)]
        # Capture the created attachments during the shipping process
        current_attachments = self.env["ir.attachment"].search(domain, order="id")
        res = super().send_shipping(pickings)
        new_attachments = (
            self.env["ir.attachment"].search(domain, order="id") - current_attachments
        )
        if new_attachments:
            self._print_carrier_label(new_attachments)
        return res

    def _print_carrier_label(self, attachments):
        """
        Print the attachments according to the report behaviour.
        """
        behaviour = self.label_report_id.behaviour()
        printer = behaviour.get("printer")
        if not printer or behaviour.get("action") != "server":
            return
        WizardPrintAttachment = self.env["wizard.print.attachment"]
        wizard_print = WizardPrintAttachment.create(
            {
                "printer_id": printer.id,
                "attachment_line_ids": [
                    Command.create(
                        {"attachment_id": attachment.id},
                    )
                    for attachment in attachments
                ],
            }
        )
        wizard_print.print_attachments()
