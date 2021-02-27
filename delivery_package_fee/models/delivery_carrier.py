# Copyright 2020 Camptocamp
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    package_fee_ids = fields.One2many(
        comodel_name="delivery.package.fee",
        inverse_name="carrier_id",
    )
