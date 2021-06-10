# Copyright 2021 Camptocamp SA - Iván Todorovich
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    city_ids = fields.Many2many(
        "res.city",
        relation="delivery_carrier_city_rel",
        column1="carrier_id",
        column2="city_id",
        string="Cities",
    )

    def _match_address(self, partner):
        # Override to account for city_ids
        if self.city_ids and partner.city_id not in self.city_ids:
            return False
        return super()._match_address(partner)
