# Copyright (c) 2026 Groupe Voltaire
# @author Emilie SOUTIRAS <emilie.soutiras@groupevoltaire.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from collections import Counter

from odoo import _, fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    zpl_label_count = fields.Integer(
        string="ZPL Labels",
        compute="_compute_zpl_label_count",
    )

    def _zpl_label_attachment_domain(self):
        return [
            ("res_model", "=", self._name),
            ("res_id", "in", self.ids),
            ("name", "=ilike", "%.zpl"),
        ]

    def _compute_zpl_label_count(self):
        attachments = self.env["ir.attachment"].search(
            self._zpl_label_attachment_domain()
        )
        counts = Counter(attachments.mapped("res_id"))
        for picking in self:
            picking.zpl_label_count = counts.get(picking.id, 0)

    def action_open_zpl_label_viewer(self):
        self.ensure_one()
        attachment = self.env["ir.attachment"].search(
            self._zpl_label_attachment_domain(), order="create_date asc", limit=1
        )
        return {
            "type": "ir.actions.act_window",
            "name": _("ZPL Labels"),
            "res_model": "delivery.zpl.label.viewer",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_picking_id": self.id,
                "default_attachment_id": attachment.id,
            },
        }
