# Copyright 2021 Camptocamp
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    partner_default_delivery_carrier_id = fields.Many2one("delivery.carrier")

    def get_values(self):
        return dict(
            super().get_values() or {},
            partner_default_delivery_carrier_id=self.env["ir.default"]
            .sudo()
            .get(
                "res.partner",
                "property_delivery_carrier_id",
                company_id=self.env.company.id,
            ),
        )

    def set_values(self):
        super().set_values()
        self.env["ir.default"].sudo().set(
            "res.partner",
            "property_delivery_carrier_id",
            self.partner_default_delivery_carrier_id.id,
            company_id=self.env.company.id,
        )
