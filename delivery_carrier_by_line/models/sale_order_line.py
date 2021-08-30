# Copyright 2021 Camptocamp
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    carrier_id = fields.Many2one(
        "delivery.carrier",
        state="draft,cancel",
        domain="[('invoice_policy', '!=', 'real')]",
    )
