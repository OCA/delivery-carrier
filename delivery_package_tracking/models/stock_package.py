# Copyright 2026 Jarsa
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo import api, fields, models


class StockPackage(models.Model):
    _inherit = "stock.package"

    carrier_tracking_ref = fields.Char(
        string="Tracking Reference",
        copy=False,
        help="Tracking reference the carrier gave to this package.",
    )
    carrier_tracking_url = fields.Char(
        compute="_compute_carrier_tracking_url",
        help="Tracking page of this package on the website of the carrier.",
    )

    @api.depends("carrier_tracking_ref", "picking_ids.carrier_id.tracking_url")
    def _compute_carrier_tracking_url(self):
        for package in self:
            carrier = package.picking_ids.carrier_id[:1]
            package.carrier_tracking_url = carrier._get_package_tracking_link(
                package.carrier_tracking_ref
            )
