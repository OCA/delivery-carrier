# Copyright 2024 ACSONE SA/NV (https://www.acsone.eu)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class ChooseDeliveryPackage(models.TransientModel):

    _inherit = "choose.delivery.package"

    package_type_domain = fields.Binary(
        compute="_compute_package_type_domain", readonly=True
    )

    @api.depends_context("current_package_carrier_type")
    @api.depends("picking_id")
    def _compute_package_type_domain(self):
        package_carrier_type = self.env.context.get(
            "current_package_carrier_type", "none"
        )
        domain = [("package_carrier_type", "=", package_carrier_type)]
        for wizard in self:
            wizard.package_type_domain = domain
