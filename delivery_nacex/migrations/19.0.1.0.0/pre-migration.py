import logging

from odoo.tools.sql import column_exists, rename_column

_logger = logging.getLogger(__name__)

_CARRIER_COLUMN_RENAMES = [
    ("del_cli", "nacex_agency_code"),
    ("num_cli", "nacex_customer_code"),
    ("tip_ser", "nacex_service_code"),
    ("tip_cob", "nacex_carriage_code"),
    ("tip_env", "nacex_packaging_code"),
]


def migrate(cr, version):
    if not version:
        return

    # Rename carrier fields from NACEX API names to descriptive Odoo names
    for old_name, new_name in _CARRIER_COLUMN_RENAMES:
        if column_exists(cr, "delivery_carrier", old_name):
            _logger.info("Renaming delivery_carrier.%s -> %s", old_name, new_name)
            rename_column(cr, "delivery_carrier", old_name, new_name)

    # Migrate bultos_vts -> number_of_packages (from delivery_package_number)
    if column_exists(cr, "stock_picking", "bultos_vts"):
        _logger.info("Migrating bultos_vts -> number_of_packages on stock_picking")
        if not column_exists(cr, "stock_picking", "number_of_packages"):
            cr.execute(
                "ALTER TABLE stock_picking ADD COLUMN number_of_packages integer"
            )
        cr.execute("""
            UPDATE stock_picking
            SET number_of_packages = bultos_vts
            WHERE bultos_vts IS NOT NULL
              AND bultos_vts > 0
              AND (number_of_packages IS NULL OR number_of_packages = 0)
        """)
        cr.execute("ALTER TABLE stock_picking DROP COLUMN bultos_vts")

    # Migrate NACEX credentials from res.company to carrier.account
    _migrate_credentials_to_carrier_account(cr)


def _migrate_credentials_to_carrier_account(cr):
    """Create carrier.account records from res.company NACEX credentials
    and link them to existing NACEX delivery carriers."""
    if not column_exists(cr, "res_company", "nacex_user_name"):
        return

    cr.execute("""
        SELECT id, name, nacex_user_name, nacex_user_pass
        FROM res_company
        WHERE nacex_user_name IS NOT NULL
          AND nacex_user_pass IS NOT NULL
    """)
    companies = cr.fetchall()
    if not companies:
        return

    _logger.info("Migrating NACEX credentials from res.company to carrier.account")

    # Ensure carrier_account table exists
    cr.execute("""
        SELECT 1 FROM information_schema.tables
        WHERE table_name = 'carrier_account'
    """)
    if not cr.fetchone():
        return

    for company_id, company_name, username, password in companies:
        account_name = f"NACEX - {company_name}"
        cr.execute(
            """
            INSERT INTO carrier_account
                (name, delivery_type, account, password, company_id,
                 create_uid, write_uid, create_date, write_date)
            VALUES
                (%s, 'nacex', %s, %s, %s, 1, 1, now(), now())
            RETURNING id
            """,
            (account_name, username, password, company_id),
        )
        account_id = cr.fetchone()[0]
        _logger.info(
            "Created carrier.account %s (id=%s) for company %s",
            account_name,
            account_id,
            company_name,
        )

        # Link NACEX carriers of this company to the new account
        if column_exists(cr, "delivery_carrier", "carrier_account_id"):
            cr.execute(
                """
                UPDATE delivery_carrier
                SET carrier_account_id = %s
                WHERE delivery_type = 'nacex'
                  AND (company_id = %s OR company_id IS NULL)
                  AND carrier_account_id IS NULL
                """,
                (account_id, company_id),
            )

