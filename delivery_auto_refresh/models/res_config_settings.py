# Copyright 2023 Tecnativa - Pilar Vargas Moreno
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    set_default_carrier = fields.Boolean(
        "Set Default Carrier Automatically",
        config_parameter="delivery_auto_refresh.set_default_carrier",
    )
    auto_add_delivery_line = fields.Boolean(
        "Add Delivery Line Automatically",
        config_parameter="delivery_auto_refresh.auto_add_delivery_line",
    )
    refresh_after_picking = fields.Boolean(
        "Refresh After Picking Automatically",
        config_parameter="delivery_auto_refresh.refresh_after_picking",
    )
    auto_void_delivery_line = fields.Boolean(
        "Void delivery lines automatically",
        config_parameter="delivery_auto_refresh.auto_void_delivery_line",
    )
