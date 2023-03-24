# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class StockPickingType(models.Model):

    _inherit = "stock.picking.type"

    launch_delivery_package_wizard = fields.Boolean(
        help="When doing Put In Pack, launch the wizard to allow choosing the "
        "Delivery Package Type"
    )
