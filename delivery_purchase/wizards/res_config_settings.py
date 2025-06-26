# Copyright 2025 Tecnativa - Carlos Roca
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    recompute_delivery_price_on_picking = fields.Boolean(
        string="Recompute Delivery Price When Validate Picking",
        config_parameter="delivery_purchase.use_delivered_qty_to_set_cost",
    )
    no_create_delivery_line_on_po = fields.Boolean(
        string="Avoid Creation Of Delivery Line On Purchase Order",
        config_parameter="delivery_purchase.no_create_delivery_line_on_po",
    )
