# Copyright 2025 Nitrokey GmbH
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    declared_amount = fields.Float(
        string="Declared Amount (%)",
        default=100.0,
        help="Percentage of the sale price to be used as the declared value for shipping. "
        "100% means the full sale price will be used.",
    )
