# Copyright 2024 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging

from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)


@openupgrade.migrate()
def migrate(env, version):
    _logger.info("Move final_shipping_partner_id from procurement_group to stock_move")
    openupgrade.logged_query(
        env.cr,
        """
        ALTER TABLE stock_move
        ADD COLUMN final_shipping_partner_id INTEGER
        """,
    )
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE stock_move sm
        SET final_shipping_partner_id = pg.final_shipping_partner_id
        FROM procurement_group pg
        WHERE sm.group_id = pg.id
        """,
    )
