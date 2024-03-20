# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import logging

from openupgradelib import openupgrade

from odoo.tools import sql

_logger = logging.getLogger(__name__)


def _update_from_res_company_to_delivery_carrier(env):
    _logger.info("update from res_company to delivery_carrier")
    company_id = env.ref("base.main_company").id
    if sql.column_exists(env.cr, "res_company", "gls_contact_id"):
        # update value in delivery.carrier from res_company gls_contact_id
        env.cr.execute(
            f"""UPDATE delivery_carrier
        SET gls_contact_id =
            (SELECT gls_contact_id FROM res_company WHERE id={company_id})
        WHERE delivery_type like 'gls'"""
        )
        #  remove gls_contact_id from res_company
        env.cr.execute("ALTER TABLE res_company DROP COLUMN gls_contact_id")


def _update_from_delivery_carrier_to_carrier_account(env):
    _logger.info("update value in carrier.account from delivery.carrier")
    for column in ("gls_login", "gls_password"):
        if sql.column_exists(env.cr, "delivery.carrier", column):
            # update column value in carrier_account
            env.cr.execute(
                f"""UPDATE carrier_account
            SET {column} =
                (SELECT {column} FROM delivery_carrier WHERE delivery_type like 'gls')
            WHERE delivery_type like 'gls'"""
            )
            # remove column from delivery.carrier
            env.cr.execute(f"ALTER TABLE delivery_carrier DROP COLUMN {column}")


@openupgrade.migrate()
def migrate(env, version):
    _update_from_res_company_to_delivery_carrier(env)
    _update_from_delivery_carrier_to_carrier_account(env)
