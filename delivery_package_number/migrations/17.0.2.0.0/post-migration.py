# Copyright 2026 Tecnativa - Sergio Teruel
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from openupgradelib import openupgrade


def _column_exists_and_is_boolean(cr, table_name, column_name):
    cr.execute(
        """
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = current_schema()
          AND table_name = %s
          AND column_name = %s
          AND data_type = 'boolean'
        """,
        (table_name, column_name),
    )
    return bool(cr.fetchone())


@openupgrade.migrate()
def migrate(env, version):
    legacy_column = openupgrade.get_legacy_name("force_set_number_of_packages")
    if _column_exists_and_is_boolean(env.cr, "stock_picking_type", legacy_column):
        sql = f"""
            UPDATE stock_picking_type
            SET force_set_number_of_packages='always'
            WHERE force_set_number_of_packages IS NULL AND {legacy_column} = true;
        """
        openupgrade.logged_query(env.cr, sql)
