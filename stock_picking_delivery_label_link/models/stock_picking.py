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

    def send_to_shipper(self):
        # Shipping labels are attached to the record during this method. There's no
        # core hook method for this, and we want to avoid pulling a dependency in
        # every carrier implementation.
        previous_attachments = self.allowed_shipping_attachement_ids
        result = super().send_to_shipper()
        self._compute_allowed_shipping_attachement_ids()
        self.shipping_label_ids = (
            self.allowed_shipping_attachement_ids - previous_attachments
        )
        return result
