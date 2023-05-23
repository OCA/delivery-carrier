# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class DeliveryCarrier(models.Model):

    _inherit = "delivery.carrier"

    automatic_package_creation_at_delivery = fields.Boolean(
        default=lambda self: self.env.company.automatic_package_creation_at_delivery_default,
        help="Check this in order to create automatically a delivery package for this carrier"
        "for the delivery picking.",
    )
