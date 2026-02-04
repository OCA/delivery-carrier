# Copyright 2025 ACSONE SA/NV
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models


class DeliveryCarrier(models.Model):
    _name = "delivery.carrier"
    _inherit = ["delivery.carrier", "image.mixin"]

    has_image = fields.Boolean(compute="_compute_has_image")

    @api.depends("image_128")
    def _compute_has_image(self):
        for carrier in self:
            carrier.has_image = bool(carrier.image_128)
