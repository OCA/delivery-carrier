# Copyright 2026 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    if openupgrade.table_exists(
        env.cr, "delivery_carrier_limited_amount_rel"
    ) and not openupgrade.table_exists(
        env.cr, "adr_limited_amount_delivery_carrier_rel"
    ):
        # limited.amount becomes adr.limited.amount, the model has already been renamed
        # in community-data-files/l10n_eu_product_adr_dangerous_goods migration, here we
        # just need to rename the relation table of the many2many field we add in the
        # current module (and the concerned column)
        openupgrade.rename_columns(
            env.cr,
            {
                "delivery_carrier_limited_amount_rel": [
                    ("limited_amount_id", "adr_limited_amount_id")
                ]
            },
        )
        openupgrade.rename_tables(
            env.cr,
            [
                (
                    "delivery_carrier_limited_amount_rel",
                    "adr_limited_amount_delivery_carrier_rel",
                )
            ],
        )
