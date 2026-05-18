# Copyright 2026 Camptocamp SA (https://www.camptocamp.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import models
from odoo.osv.expression import AND, OR


class ChooseDeliveryPackage(models.TransientModel):
    _inherit = "choose.delivery.package"

    def _compute_package_type_domain(self):
        package_carrier = self.picking_id.carrier_id
        domain = super()._compute_package_type_domain() or []
        if not package_carrier:
            return domain
        # if package has specific carrier defined, use that for the domain
        package_carrier_domain = OR(
            [
                [("allowed_package_carrier_ids", "=", False)],
                [("allowed_package_carrier_ids", "in", [package_carrier.id])],
            ]
        )
        domain = AND([domain, package_carrier_domain])
        self.package_type_domain = domain
