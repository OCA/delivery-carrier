# Copyright 2026 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    # The field set_delivery_package_type_on_put_in_pack moved
    # from stock_picking_delivery_link
    # to stock_picking_delivery_package_type_domain.
    # It got renamed filter_package_type_on_put_in_pack.
    # The old stock_picking_delivery_link view still uses the old field.
    # That view must be deleted first,
    # or the stock_picking_delivery_package_type_domain view fails validation.
    openupgrade.delete_records_safely_by_xml_id(
        env, ["stock_picking_delivery_link.stock_picking_type_form_view"]
    )
