# Copyright 2023 ACSONE SA/NV (https://www.acsone.eu)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class StockPickingType(models.Model):
    _inherit = "stock.picking.type"

    set_delivery_package_type_on_put_in_pack = fields.Boolean(
        "Delivery package type on put in pack"
    )
