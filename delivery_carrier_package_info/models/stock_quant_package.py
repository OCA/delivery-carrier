# Copyright 2020 Akretion (https://www.akretion.com).
# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class StockQuantPackage(models.Model):
    _inherit = "stock.quant.package"

    parcel_tracking = fields.Char()
    parcel_tracking_uri = fields.Char(
        help="Link to the carrier's tracking page for this package."
    )

    @api.depends("parcel_tracking", "name")
    def _compute_display_name(self):
        res = super()._compute_display_name()
        for pack in self:
            if pack.parcel_tracking:
                pack.display_name = f"{pack.display_name} - {pack.parcel_tracking}"
        return res

    def open_website_url(self):
        """Implement you own action in your module"""
        return None
