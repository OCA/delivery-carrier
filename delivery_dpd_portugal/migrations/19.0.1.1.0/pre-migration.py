# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tools import sql


def migrate(cr, version):
    """Migrate delivery_type from 'dpd_portugal' to 'dpd_pt'."""
    if not version:
        return

    # Update delivery.carrier records
    cr.execute(
        """
        UPDATE delivery_carrier
        SET delivery_type = 'dpd_pt'
        WHERE delivery_type = 'dpd_portugal'
        """
    )

    # Migrate prod_environment from old custom field to standard field
    # The prod_environment field already exists in base delivery module
    if sql.column_exists(cr, "delivery_carrier", "dpd_portugal_prod_environment"):
        cr.execute(
            """
            UPDATE delivery_carrier
            SET prod_environment = dpd_portugal_prod_environment
            WHERE delivery_type = 'dpd_pt'
            AND dpd_portugal_prod_environment = TRUE
            """
        )
        # Drop the old column
        cr.execute(
            """
            ALTER TABLE delivery_carrier
            DROP COLUMN IF EXISTS dpd_portugal_prod_environment
            """
        )
