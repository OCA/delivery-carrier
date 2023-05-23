# Copyright 2023 Tecnativa - Pilar Vargas
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    """Remove system parameter records of 'delivery_auto_refresh' with value 0 or False,
    to avoid their activation during migration due to their presence in the database."""
    openupgrade.logged_query(
        env.cr,
        """
        DELETE FROM ir_config_parameter
        WHERE key LIKE '%delivery_auto_refresh%'
        AND (value = '0' OR value = 'False')
        """,
    )
