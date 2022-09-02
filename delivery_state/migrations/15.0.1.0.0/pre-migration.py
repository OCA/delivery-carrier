# Copyright 2022 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    old_template = env.ref("delivery_state.delivery_notification")
    new_template = env.ref("stock.mail_template_data_delivery_confirmation")
    items = env["res.company"].search(
        [("stock_mail_confirmation_template_id", "=", old_template.id)]
    )
    items.write({"stock_mail_confirmation_template_id": new_template.id})
