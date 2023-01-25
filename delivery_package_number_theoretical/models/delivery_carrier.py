# Copyright 2021 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class DeliveryCarrier(models.Model):

    _inherit = "delivery.carrier"

    maximum_weight_per_package = fields.Float(string="Maximum weight per package")
