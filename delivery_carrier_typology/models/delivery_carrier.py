# Copyright 2025 Akretion (https://www.akretion.com).
# @author Kévin Roche <kevin.roche@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    carrier_typology_id = fields.Many2one(
        "delivery.carrier.typology",
        string="Delivery Carrier Typology",
        compute="_compute_carrier_typology_id",
        readonly=True,
    )

    def _compute_carrier_typology_id(self):
        for rec in self:
            carrier_types = self.env["delivery.carrier.typology"].search(
                [("carrier_id", "=", rec.id)],
            )
            if carrier_types:
                if rec.company_id:
                    carrier_types = carrier_types.filtered(
                        lambda ct: rec.company_id in ct.company_ids
                    )
                else:
                    carrier_types = carrier_types.filtered(
                        lambda ct, self=self: not ct.company_ids
                        or self.env.company in ct.company_ids
                    )

            rec.carrier_typology_id = carrier_types[0] if carrier_types else False
