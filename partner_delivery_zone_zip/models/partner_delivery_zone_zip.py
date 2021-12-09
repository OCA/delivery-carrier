# Copyright 2021 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class PartnerDeliveryZoneZip(models.Model):

    _name = "partner.delivery.zone.zip"
    _description = "Partner Delivery Zone Zip"

    name = fields.Char(
        required=True,
        string="ZIP",
    )
    delivery_zone_id = fields.Many2one(
        comodel_name="partner.delivery.zone",
        string="Delivery Zone",
        required=True,
    )

    _sql_constraints = [
        ("name_uniq", "unique (name)", "ZIP for Delivery Zones should be unique!"),
    ]
