# Copyright 2025 Akretion (https://www.akretion.com).
# @author Kévin Roche <kevin.roche@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class ChooseDeliveryCarrier(models.TransientModel):
    _inherit = "choose.delivery.carrier"

    carrier_id = fields.Many2one(
        compute="_compute_carrier_id",
        readonly=False,
        store=True,
    )

    carrier_typology_id = fields.Many2one(
        "delivery.carrier.typology",
        string="Delivery Carrier Typology",
    )

    @api.depends("carrier_typology_id")
    def _compute_carrier_id(self):
        for rec in self:
            if rec.carrier_typology_id:
                rec.carrier_id = rec.carrier_typology_id.carrier_id
