# Copyright 2026 Moduon
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    one_delivery_fee_by_sale_order = fields.Boolean(
        help="The delivery fee will be applied just once to the order",
    )
    one_delivery_fee_by_commercial_partner_day = fields.Boolean(
        help="The delivery fee will be applied just once per commercial partner "
        "and day",
    )
