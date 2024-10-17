# Copyright 2024 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    allowed_shipping_attachement_ids = fields.Many2many(
        comodel_name="ir.attachment",
        compute="_compute_allowed_shipping_attachement_ids",
    )
    shipping_label_ids = fields.Many2many(
        comodel_name="ir.attachment",
        # We don't want the attachment to be deleted by mistake
        ondelete="restrict",
        domain="[('id', 'in', allowed_shipping_attachement_ids)]",
    )

    def _compute_allowed_shipping_attachement_ids(self):
        for picking in self:
            picking.allowed_shipping_attachement_ids = self.env["ir.attachment"].search(
                [("res_model", "=", self._name), ("res_id", "=", picking.id)]
            )
