# Copyright 2021 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


class ResPartner(models.Model):

    _inherit = "res.partner"

    @api.onchange("zip")
    def onchange_zip(self):
        delivery_zone_zip = self.env["partner.delivery.zone.zip"].search(
            [("name", "=", self.zip)], limit=1
        )
        self.delivery_zone_id = delivery_zone_zip.delivery_zone_id
