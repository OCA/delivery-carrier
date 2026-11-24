# Copyright 2026 Nitrokey GmbH
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class ChooseDeliveryCarrier(models.TransientModel):
    _inherit = "choose.delivery.carrier"

    ups_landed_cost_amount = fields.Monetary(
        string="Duties, Taxes & Fees",
        related="order_id.ups_landed_cost_amount",
        currency_field="currency_id",
        readonly=True,
    )
    ups_landed_cost_estimate_amount = fields.Monetary(
        string="Estimated Duties, Taxes & Fees",
        related="order_id.ups_landed_cost_estimate_amount",
        currency_field="currency_id",
        readonly=True,
    )
