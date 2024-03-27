# Copyright 2023 Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    prohibited_shipping_means_ids = fields.Many2many(
        "delivery.carrier.typology", related="product_id.prohibited_shipping_means_ids"
    )
