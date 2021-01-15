# Copyright 2021 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from openupgradelib import openupgrade  # pylint: disable=W7936


@openupgrade.migrate()
def migrate(env, version):
    """We'll be using the former template in this module"""
    if not openupgrade.column_exists(
        env.cr, "res_company", "send_delivery_confirmation"
    ):
        return
    delivery_template_id = env.ref("delivery_state.delivery_notification").id
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE res_company SET
            stock_move_email_validation = send_delivery_confirmation,
            stock_mail_confirmation_template_id = %s
        """,
        [delivery_template_id],
    )
