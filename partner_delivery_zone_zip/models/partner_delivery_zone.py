# Copyright 2021 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class PartnerDeliveryZone(models.Model):

    _inherit = "partner.delivery.zone"

    zip_ids = fields.One2many(
        comodel_name="partner.delivery.zone.zip",
        inverse_name="delivery_zone_id",
        string="ZIPs",
    )
