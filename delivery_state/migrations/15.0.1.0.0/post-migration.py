# Copyright 2023 Tecnativa - David Vidal
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.load_data(
        env.cr, "delivery_state", "migrations/15.0.1.0.0/noupdate_changes.xml"
    )
    openupgrade.delete_record_translations(
        env.cr,
        "delivery_state",
        [
            "delivery_notification",
        ],
    )
