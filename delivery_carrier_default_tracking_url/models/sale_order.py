# Copyright 2019 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class SaleOrder(models.Model):

    _inherit = "sale.order"

    default_tracking_url = fields.Char(
        related="carrier_id.default_tracking_url", readonly=True
    )
