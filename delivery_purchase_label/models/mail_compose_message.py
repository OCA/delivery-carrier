# Copyright 2024 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import api, models


class MailComposer(models.TransientModel):
    _inherit = "mail.compose.message"

    @api.model
    def generate_email_for_composer(self, template_id, res_ids, fields):
        res = super().generate_email_for_composer(template_id, res_ids, fields)
        if self.model != "purchase.order":
            return res
        if (
            template_id
            in self.env["purchase.order"]._mail_templates_to_not_attach_labels()
        ):
            return
        purchase_orders = self.env["purchase.order"].browse(res_ids)
        for order in purchase_orders:
            # Add the labels generated when sending the order by email
            label_picking = order.delivery_label_picking_id
            if not label_picking:
                continue
            attachments = self.env["ir.attachment"].search(
                [
                    ("res_model", "=", label_picking._name),
                    ("res_id", "=", label_picking.id),
                ]
            )
            if attachments:
                attachment_ids = (
                    res[order.id].get("attachment_ids", []) + attachments.ids
                )
                res[order.id]["attachment_ids"] = attachment_ids
        return res
