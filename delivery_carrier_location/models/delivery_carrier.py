# Copyright 2021 Camptocamp SA - Iván Todorovich
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    zip_ids = fields.Many2many(
        "res.city.zip",
        relation="delivery_carrier_zip_rel",
        column1="carrier_id",
        column2="zip_id",
        string="Zip codes",
    )

    def _match_address(self, partner):
        # Override to account for city_ids and zip_ids
        res = super()._match_address(partner)
        # Fail quickly if super already rejected it
        if not res or not self.zip_ids:
            return res  # pragma: no cover
        # Check partner's zip.
        partner_zip = (partner.zip or partner.zip_id.name or "").upper()
        return partner_zip in {r.name.upper() for r in self.zip_ids}
