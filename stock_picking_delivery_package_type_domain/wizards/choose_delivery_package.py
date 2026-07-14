# Copyright 2024 ACSONE SA/NV (https://www.acsone.eu)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class ChooseDeliveryPackage(models.TransientModel):
    _inherit = "choose.delivery.package"

    package_type_domain = fields.Binary(
        compute="_compute_package_type_domain", readonly=True
    )

    @api.depends(
        "picking_id.carrier_id",
        "picking_id.picking_type_id.filter_package_type_on_put_in_pack",
    )
    def _compute_package_type_domain(self):
        for wizard in self:
            if not wizard.picking_id.picking_type_id.filter_package_type_on_put_in_pack:
                wizard.package_type_domain = []
                continue
            carrier = wizard.picking_id.carrier_id
            if carrier:
                package_carrier_type = carrier.delivery_type
                if package_carrier_type in ("fixed", "base_on_rule", "pricelist"):
                    package_carrier_type = "none"
            else:
                package_carrier_type = False
            wizard.package_type_domain = [
                ("package_carrier_type", "=", package_carrier_type)
            ]
