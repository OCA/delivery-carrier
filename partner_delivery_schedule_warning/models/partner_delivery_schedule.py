# Copyright 2026 NICO SOLUTIONS - Nils Coenen
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, models


class DeliverySchedule(models.Model):
    _inherit = "delivery.schedule"

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if "partner_ids" in vals:
                vals["partner_ids"] = [(6, 0, vals["partner_ids"])]

        records = super().create(vals_list)

        partner_ids = records.mapped("partner_ids").ids
        if partner_ids:
            pickings = self.env["stock.picking"].search(
                [
                    ("partner_id", "in", partner_ids),
                    ("state", "not in", ["done", "cancel"]),
                ]
            )
            pickings._compute_partner_delivery_schedule_warning()

        return records

    def write(self, vals):
        res = super().write(vals)
        trigger_fields = {
            "hour_from",
            "hour_to",
            "monday",
            "tuesday",
            "wednesday",
            "thursday",
            "friday",
            "saturday",
            "sunday",
            "partner_ids",
        }

        if set(vals.keys()) & trigger_fields:
            partners = self.env["res.partner"].search(
                [("delivery_schedule_ids", "in", self.ids)]
            )
            if partners:
                pickings = self.env["stock.picking"].search(
                    [
                        ("partner_id", "in", partners.ids),
                        ("state", "not in", ["done", "cancel"]),
                    ]
                )
                pickings._compute_partner_delivery_schedule_warning()

        return res
