# Copyright 2024 Moduon Team S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)

import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    with api.Environment.manage():
        env = api.Environment(cr, SUPERUSER_ID, {})
        partners = (
            env["carrier.driver"]
            .search([("driver_id", "!=", False)])
            .mapped("driver_id")
        )
        partners.write({"is_driver": True})
