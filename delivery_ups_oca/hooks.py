# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.tools.sql import column_exists, create_column


def create_declared_value_columns(cr):
    if not column_exists(cr, "stock_picking", "declared_value_currency_id"):
        create_column(cr, "stock_picking", "declared_value_currency_id", "int4")
        cr.execute(
            """
            UPDATE stock_picking sp
            SET declared_value_currency_id = COALESCE(so.currency_id, rc.currency_id)
            FROM stock_picking sp2
            LEFT JOIN sale_order so ON so.id = sp2.sale_id
            LEFT JOIN res_company rc ON rc.id = sp2.company_id
            WHERE sp2.id = sp.id
            """
        )
    if not column_exists(cr, "stock_picking", "declared_value"):
        create_column(cr, "stock_picking", "declared_value", "numeric")


def pre_init_hook(env):
    create_declared_value_columns(env.cr)
