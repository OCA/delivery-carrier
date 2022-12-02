# Copyright 2022 Coop IT Easy SC
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    tentative_carrier = fields.Many2one(
        comodel_name="delivery.carrier",
        string="Tentative Delivery Method",
    )
