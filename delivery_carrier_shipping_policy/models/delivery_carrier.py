# Copyright 2025 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import fields, models


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    picking_policy = fields.Selection(
        [("direct", "As soon as possible"), ("one", "When all products are ready")],
        string="Shipping Policy",
        help="Shipping policy to use on sales orders.",
    )
