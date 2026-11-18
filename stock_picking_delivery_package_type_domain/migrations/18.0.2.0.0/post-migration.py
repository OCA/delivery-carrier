# Copyright 2026 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openupgradelib import openupgrade


def migrate(cr, version):
    # The config previously lived in stock_picking_delivery_link as
    # set_delivery_package_type_on_put_in_pack. Copy it over
    if not openupgrade.column_exists(
        cr, "stock_picking_type", "set_delivery_package_type_on_put_in_pack"
    ):
        return
    openupgrade.logged_query(
        cr,
        """
        UPDATE stock_picking_type
        SET filter_package_type_on_put_in_pack =
            set_delivery_package_type_on_put_in_pack
        WHERE set_delivery_package_type_on_put_in_pack IS NOT NULL
        """,
    )
