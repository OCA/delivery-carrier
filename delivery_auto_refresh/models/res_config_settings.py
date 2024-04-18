# Copyright 2023 Tecnativa - Pilar Vargas Moreno
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    # Migration Note 17.0: move this to module sale_order_carrier_auto_assign
    sale_auto_assign_carrier_on_create = fields.Boolean(
        related="company_id.sale_auto_assign_carrier_on_create",
        readonly=False,
    )
    # End migration note

    auto_add_delivery_line = fields.Boolean(
        "Refresh shipping cost line automatically",
        config_parameter="delivery_auto_refresh.auto_add_delivery_line",
    )
    refresh_after_picking = fields.Boolean(
        "Refresh after picking automatically",
        config_parameter="delivery_auto_refresh.refresh_after_picking",
    )
    auto_void_delivery_line = fields.Boolean(
        "Void delivery lines automatically",
        config_parameter="delivery_auto_refresh.auto_void_delivery_line",
    )
