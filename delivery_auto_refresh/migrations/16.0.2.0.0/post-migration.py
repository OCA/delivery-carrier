# Copyright 2024 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import SUPERUSER_ID, api


def _migrate_setting_to_company(env):
    if env["ir.config_parameter"].get_param(
        "delivery_auto_refresh.set_default_carrier"
    ):
        env["res.company"].search([]).sale_auto_assign_carrier_on_create = True

    if env["ir.config_parameter"].get_param(
        "delivery_auto_refresh.auto_add_delivery_line"
    ):
        env["res.company"].search([]).sale_auto_add_delivery_line = True

    if env["ir.config_parameter"].get_param(
        "delivery_auto_refresh.refresh_after_picking"
    ):
        env["res.company"].search([]).sale_refresh_delivery_after_picking = True

    if env["ir.config_parameter"].get_param(
        "delivery_auto_refresh.auto_void_delivery_line"
    ):
        env["res.company"].search([]).sale_auto_void_delivery_line = True


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    _migrate_setting_to_company(env)
