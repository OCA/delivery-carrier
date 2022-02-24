# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tools.misc import str2bool


def get_bool_param(env, name, default="0"):
    get_param = env["ir.config_parameter"].sudo().get_param
    param = "delivery_auto_refresh." + name
    return str2bool(get_param(param, ""), default=default)
