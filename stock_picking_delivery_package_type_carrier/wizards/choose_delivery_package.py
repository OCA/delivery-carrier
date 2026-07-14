# Copyright 2026 Camptocamp SA (https://www.camptocamp.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import models
from odoo.osv.expression import AND, OR


class ChooseDeliveryPackage(models.TransientModel):
    _inherit = "choose.delivery.package"

    def _compute_package_type_domain(self):
        res = super()._compute_package_type_domain()
        for wizard in self:
            package_carrier = wizard.picking_id.carrier_id
            if package_carrier and wizard.package_type_domain:
                # if package has specific carrier defined, use that for the domain
                package_carrier_domain = OR(
                    [
                        [("allowed_package_carrier_ids", "=", False)],
                        [("allowed_package_carrier_ids", "in", [package_carrier.id])],
                    ]
                )
                wizard.package_type_domain = AND(
                    [wizard.package_type_domain, package_carrier_domain]
                )
        return res
