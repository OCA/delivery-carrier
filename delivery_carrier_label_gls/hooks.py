# Copyright 2021 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import SUPERUSER_ID, api


def post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    rcs = env["res.config.settings"].create({"company_id": env.company.id})
    rcs.group_stock_tracking_lot = True
    rcs.execute()
