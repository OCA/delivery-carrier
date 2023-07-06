# Copyright 2023 Tecnativa - Carlos Roca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    """Delete noupdate record because the xml_id is deprecated in favor of
    stock.mail_template_data_delivery_confirmation.
    """
    openupgrade.delete_records_safely_by_xml_id(
        env, ["delivery_state.delivery_notification"]
    )
