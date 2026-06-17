# Copyright 2026 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    delivery_schedule_ids = fields.Many2many(
        domain="[('id', 'in', delivery_zone_id.delivery_schedule_ids.ids"
        " if delivery_zone_id else [])]",
    )

    @api.onchange("delivery_zone_id")
    def onchange_delivery_zone_id(self):
        if self.delivery_zone_id:
            self.delivery_schedule_ids = self.delivery_zone_id.delivery_schedule_ids
