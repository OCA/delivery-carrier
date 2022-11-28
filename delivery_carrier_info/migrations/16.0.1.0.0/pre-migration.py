# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    if openupgrade.column_exists(env.cr, "delivery_carrier", "description"):
        env.cr.execute(
            """
            SELECT id, description
            FROM delivery_carrier
            WHERE description IS NOT NULL AND carrier_description IS NULL
        """
        )
        for carrier_id, description in env.cr.fetchall():
            env["delivery.carrier"].browse(carrier_id).write(
                {"carrier_description": description}
            )
