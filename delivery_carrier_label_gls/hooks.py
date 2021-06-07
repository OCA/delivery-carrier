# -*- coding: utf-8 -*-
# Copyright 2021 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import SUPERUSER_ID, api


def pre_init_hook(cr):
    env = api.Environment(cr, SUPERUSER_ID, {})
    env["stock.config.settings"].create({"group_stock_tracking_lot": 1}).execute()
