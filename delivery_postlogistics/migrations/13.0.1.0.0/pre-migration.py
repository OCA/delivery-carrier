# Copyright 2013-2016 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from openupgradelib import openupgrade  # pylint: disable=W7936


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.update_module_names(
        env.cr,
        [("delivery_carrier_label_postlogistics", "delivery_postlogistics")],
        merge_modules=True,
    )

    # Delete obsolete model
    env.cr.execute(
        """
        DELETE FROM ir_model_fields
        WHERE model_id IN
        (SELECT id FROM ir_model WHERE model IN
            ('postlogistics.auth', 'delivery.carrier.template.option'));
    """
    )

    # Remove obsolete view
    openupgrade.delete_records_safely_by_xml_id(
        env, ["delivery_postlogistics.view_postlogistics_auth_form"]
    )
