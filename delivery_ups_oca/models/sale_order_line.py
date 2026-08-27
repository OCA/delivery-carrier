# Copyright 2026 Nitrokey GmbH
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    is_ups_landed_cost = fields.Boolean(
        string="Is UPS Landed Cost",
        help="Technical flag identifying the sale order line that carries the UPS "
        "Global Checkout landed cost (duties and taxes).",
        copy=False,
    )
